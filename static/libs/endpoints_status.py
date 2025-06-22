#!/usr/bin/env python3

import json
import yaml
import csv
import time
import re
import asyncio
import aiohttp
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from prettytable import PrettyTable

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format='%(message)s'  # Simplified format for cleaner output
)
logger = logging.getLogger(__name__)

@dataclass
class EndpointStatus:
  url: str
  ping_ms: float
  status_code: Optional[int]
  endpoint_type: str
  is_healthy: bool
  is_slow: bool = False
  error: Optional[str] = None

class EndpointChecker:
  def __init__(self, config_path: str):
    self.config_path = Path(config_path)
    self.endpoints: List[EndpointStatus] = []
    self.PING_THRESHOLD = 1000  # Consider endpoints with ping > 1000ms as slow
    self.MAX_CONCURRENT_REQUESTS = 50  # Overall concurrency limit
    self.MAX_PER_DOMAIN = 10  # Max concurrent requests per domain
    self.REQUEST_TIMEOUT = 10
    self.domain_semaphores = {}  # Semaphores for per-domain rate limiting

    # RPC patterns that should be checked as RPC first
    self.RPC_PATTERNS = [
      'rpc.ankr',
      '/rpc',
      'endpoints.omni',
      'public.blast',
      'blockpi.network',
      'drpc.org'
    ]

    # RPC health check payloads
    self.ETH_HEALTH_PAYLOAD = {
      "jsonrpc": "2.0",
      "method": "eth_blockNumber",
      "params": [],
      "id": 1
    }
    self.SOLANA_HEALTH_PAYLOAD = {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "getHealth"
    }
    self.SUI_HEALTH_PAYLOAD = {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "sui_getProtocolConfig",
      "params": []
    }

    # URL regex pattern
    self.url_pattern = re.compile(
      r'https?://'
      r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
      r'localhost|'
      r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
      r'(?::\d+)?'
      r'(?:/?|[/?]\S+)(?:\s|$)',
      re.IGNORECASE
    )

  def extract_urls_from_string(self, text: str) -> Set[str]:
    """Extract URLs from a string using regex."""
    urls = set()

    # Try to parse as JSON first if it looks like a JSON array
    text = text.strip()
    if text.startswith('[') and text.endswith(']'):
      try:
        json_urls = json.loads(text)
        if isinstance(json_urls, list):
          for url in json_urls:
            if isinstance(url, str) and url.startswith('http'):
              urls.add(url.strip())
          return urls
      except json.JSONDecodeError:
        pass

    # Clean up the input string - handle quotes and common separators
    text = text.replace('""', '"')  # Handle escaped quotes in CSV
    text = text.replace('],[', ' ').replace('[', '').replace(']', '')
    text = text.replace('","', ' ').replace('",', ' ').replace(',"', ' ')

    # Find all URLs and clean them
    for url in self.url_pattern.findall(text):
      url = url.strip().rstrip(',').rstrip('"').rstrip("'").strip()
      if url and url.startswith('http'):  # Only include http(s) URLs
        urls.add(url)

    return urls

  def extract_urls_from_object(self, obj) -> Set[str]:
    """Recursively extract URLs from any object type."""
    urls = set()
    if isinstance(obj, str):
      urls.update(self.extract_urls_from_string(obj))
    elif isinstance(obj, dict):
      for value in obj.values():
        urls.update(self.extract_urls_from_object(value))
    elif isinstance(obj, (list, tuple)):
      for item in obj:
        urls.update(self.extract_urls_from_object(item))
    return urls

  def load_config(self) -> Set[str]:
    """Load URLs from various config file formats."""
    suffix = self.config_path.suffix.lower()
    urls = set()

    logger.info(f"Loading config from {self.config_path}")

    with open(self.config_path, 'r') as f:
      if suffix == '.csv':
        reader = csv.reader(f)
        for row in reader:
          # For CSV, check columns that are likely to contain URLs
          for cell in row:
            cell_urls = self.extract_urls_from_string(cell)
            urls.update(cell_urls)
      else:
        content = f.read()
        if suffix == '.json':
          try:
            data = json.loads(content)
            urls = self.extract_urls_from_object(data)
            if not urls:
              urls = self.extract_urls_from_string(content)
          except json.JSONDecodeError:
            urls = self.extract_urls_from_string(content)
        elif suffix in ['.yml', '.yaml']:
          try:
            data = yaml.safe_load(content)
            urls = self.extract_urls_from_object(data)
            if not urls:
              urls = self.extract_urls_from_string(content)
          except yaml.YAMLError:
            urls = self.extract_urls_from_string(content)
        else:
          urls = self.extract_urls_from_string(content)

    # Filter out websocket URLs
    urls = {url for url in urls if url.startswith('http')}

    # Debug output
    logger.info(f"Found {len(urls)} unique URLs:")
    for url in sorted(urls):
      logger.info(f"  - {url}")

    if not urls:
      logger.warning(f"No URLs found in {self.config_path}")

    return urls

  async def detect_endpoint_type(self, response: aiohttp.ClientResponse, url: str) -> str:
    """Detect the type of endpoint based on response and URL."""
    content_type = response.headers.get('Content-Type', '').lower()

    url_lower = url.lower()
    if any(chain in url_lower for chain in ['ethereum', 'eth', 'solana', 'sui', 'rpc']):
      return 'JSON-RPC'

    try:
      if 'application/json' in content_type:
        await response.json()  # Try parsing JSON
        return 'API'
      elif 'text/html' in content_type:
        return 'Static Website'
      elif 'application/json-rpc' in content_type:
        return 'JSON-RPC'
    except:
      pass

    return 'Unknown'

  def should_check_as_rpc_first(self, url: str) -> bool:
    """Determine if URL should be checked as RPC endpoint first."""
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in self.RPC_PATTERNS)

  async def try_rpc_health_check(self, session: aiohttp.ClientSession, url: str) -> Optional[EndpointStatus]:
    """Attempt RPC health checks for different node types."""
    start_time = time.time()
    headers = {"Content-Type": "application/json"}

    # Try standard health endpoint first
    try:
      async with session.get(f"{url.rstrip('/')}/health", timeout=self.REQUEST_TIMEOUT) as response:
        if response.status == 200:
          ping_ms = (time.time() - start_time) * 1000
          return EndpointStatus(
            url=url,
            ping_ms=ping_ms,
            status_code=200,
            endpoint_type='JSON-RPC',
            is_healthy=True,
            is_slow=ping_ms > self.PING_THRESHOLD
          )
    except:
      pass

    # Try each RPC protocol in sequence
    url_lower = url.lower()
    payloads = []

    # Determine order of protocols to try
    if 'sol' in url_lower:
      payloads = [self.SOLANA_HEALTH_PAYLOAD, self.ETH_HEALTH_PAYLOAD, self.SUI_HEALTH_PAYLOAD]
    elif 'sui' in url_lower:
      payloads = [self.SUI_HEALTH_PAYLOAD, self.ETH_HEALTH_PAYLOAD, self.SOLANA_HEALTH_PAYLOAD]
    else:
      payloads = [self.ETH_HEALTH_PAYLOAD, self.SOLANA_HEALTH_PAYLOAD, self.SUI_HEALTH_PAYLOAD]

    for payload in payloads:
      try:
        async with session.post(url, json=payload, headers=headers, timeout=self.REQUEST_TIMEOUT) as response:
          if response.status == 200:
            ping_ms = (time.time() - start_time) * 1000
            return EndpointStatus(
              url=url,
              ping_ms=ping_ms,
              status_code=response.status,
              endpoint_type='JSON-RPC',
              is_healthy=True,
              is_slow=ping_ms > self.PING_THRESHOLD
            )
      except:
        continue

    return None

  def get_domain_from_url(self, url: str) -> str:
    """Extract root domain from URL."""
    try:
      parsed = urlparse(url)
      # Get the main domain (e.g., 'ankr.com' from 'rpc.ankr.com')
      domain_parts = parsed.netloc.split('.')
      if len(domain_parts) > 2:
        return '.'.join(domain_parts[-2:])
      return parsed.netloc
    except:
      return url

  def get_domain_semaphore(self, domain: str) -> asyncio.Semaphore:
    """Get or create a semaphore for a domain."""
    if domain not in self.domain_semaphores:
      self.domain_semaphores[domain] = asyncio.Semaphore(self.MAX_PER_DOMAIN)
    return self.domain_semaphores[domain]

  async def check_endpoint_with_rate_limit(self, session: aiohttp.ClientSession, url: str) -> EndpointStatus:
    """Check endpoint with domain-based rate limiting."""
    domain = self.get_domain_from_url(url)
    domain_semaphore = self.get_domain_semaphore(domain)

    async with domain_semaphore:
      return await self.check_endpoint(session, url)

  async def check_endpoint(self, session: aiohttp.ClientSession, url: str) -> EndpointStatus:
    """Check a single endpoint and return its status."""
    start_time = time.time()

    # Check if this should be treated as RPC first
    if self.should_check_as_rpc_first(url):
      rpc_status = await self.try_rpc_health_check(session, url)
      if rpc_status:
        return rpc_status

    try:
      async with session.get(url, timeout=self.REQUEST_TIMEOUT, ssl=False) as response:
        ping_ms = (time.time() - start_time) * 1000

        # If we get a 404 and haven't tried RPC check yet, try it now
        if response.status == 404 and not self.should_check_as_rpc_first(url):
          rpc_status = await self.try_rpc_health_check(session, url)
          if rpc_status:
            return rpc_status

        endpoint_type = await self.detect_endpoint_type(response, url)
        is_healthy = response.status == 200

        return EndpointStatus(
          url=url,
          ping_ms=ping_ms,
          status_code=response.status,
          endpoint_type=endpoint_type,
          is_healthy=is_healthy,
          is_slow=ping_ms > self.PING_THRESHOLD
        )
    except asyncio.TimeoutError:
      return EndpointStatus(
        url=url,
        ping_ms=-1,
        status_code=None,
        endpoint_type='Unknown',
        is_healthy=False,
        error='Timeout'
      )
    except Exception as e:
      return EndpointStatus(
        url=url,
        ping_ms=-1,
        status_code=None,
        endpoint_type='Unknown',
        is_healthy=False,
        error=str(e)
      )

  async def check_endpoints_batch(self, urls: List[str]) -> List[EndpointStatus]:
    """Check a batch of endpoints concurrently with domain-based rate limiting."""
    connector = aiohttp.TCPConnector(limit=self.MAX_CONCURRENT_REQUESTS, force_close=True)
    timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
      tasks = [self.check_endpoint_with_rate_limit(session, url) for url in urls]
      return await asyncio.gather(*tasks)

  def report_problems(self):
    """Generate a clean tabular report of endpoint status."""
    # Create tables for different categories
    healthy_table = PrettyTable()
    healthy_table.field_names = ["URL", "Ping (ms)", "Status", "Type"]
    healthy_table.align = "l"
    healthy_table.max_width = 60

    slow_table = PrettyTable()
    slow_table.field_names = ["URL", "Ping (ms)", "Status", "Type"]
    slow_table.align = "l"
    slow_table.max_width = 60

    error_table = PrettyTable()
    error_table.field_names = ["URL", "Status", "Type", "Issue"]
    error_table.align = "l"
    error_table.max_width = 60

    healthy_count = 0
    slow_count = 0
    error_count = 0

    for endpoint in sorted(self.endpoints, key=lambda x: (x.url, x.ping_ms)):
      url_display = endpoint.url[:57] + "..." if len(endpoint.url) > 60 else endpoint.url

      if not endpoint.is_healthy:
        if endpoint.error:
          error_count += 1
          error_table.add_row([
            url_display,
            endpoint.status_code or "Error",
            endpoint.endpoint_type,
            endpoint.error
          ])
        else:
          slow_count += 1
          slow_table.add_row([
            url_display,
            f"{endpoint.ping_ms:.1f}",
            endpoint.status_code,
            endpoint.endpoint_type
          ])
      elif endpoint.is_slow:
        slow_count += 1
        slow_table.add_row([
          url_display,
          f"{endpoint.ping_ms:.1f}",
          endpoint.status_code,
          endpoint.endpoint_type
        ])
      else:
        healthy_count += 1
        healthy_table.add_row([
          url_display,
          f"{endpoint.ping_ms:.1f}",
          endpoint.status_code,
          endpoint.endpoint_type
        ])

    # Print summary and tables
    total = len(self.endpoints)
    logger.info("\n=== Endpoint Status Summary ===")
    logger.info(f"Total Endpoints: {total}")
    logger.info(f"Healthy: {healthy_count} ({(healthy_count/total*100):.1f}%)")
    logger.info(f"Slow: {slow_count} ({(slow_count/total*100):.1f}%)")
    logger.info(f"Errors: {error_count} ({(error_count/total*100):.1f}%)")

    logger.info("\n=== Healthy Endpoints ===")
    logger.info(healthy_table)

    if slow_count > 0:
      logger.info("\n=== Slow Endpoints (>1000ms) ===")
      logger.info(slow_table)

    if error_count > 0:
      logger.info("\n=== Failed Endpoints ===")
      logger.info(error_table)

  async def check_all_endpoints(self):
    """Check all endpoints from the config file with progress tracking."""
    urls = list(self.load_config())
    total_urls = len(urls)
    logger.info(f"Found {total_urls} endpoints to check")

    # Group URLs by domain for better rate limiting
    domain_groups = {}
    for url in urls:
      domain = self.get_domain_from_url(url)
      if domain not in domain_groups:
        domain_groups[domain] = []
      domain_groups[domain].append(url)

    # Process URLs in interleaved batches to distribute load
    processed = 0
    results = []
    while processed < total_urls:
      batch = []
      # Take one URL from each domain group until we reach batch size
      for domain, domain_urls in domain_groups.items():
        if domain_urls:
          batch.append(domain_urls.pop(0))
          if len(batch) >= self.MAX_CONCURRENT_REQUESTS:
            break

      if not batch:  # No more URLs to process
        break

      batch_results = await self.check_endpoints_batch(batch)
      results.extend(batch_results)
      processed += len(batch)

      # Log progress
      progress = (processed / total_urls) * 100
      logger.info(f"Progress: {processed}/{total_urls} ({progress:.1f}%)")

      # Log results as they come in
      for status in batch_results:
        if status.error:
          logger.error(f"URL: {status.url} - Error: {status.error}")
        else:
          logger.info(
            f"URL: {status.url} - Ping: {status.ping_ms:.2f}ms - "
            f"Status: {status.status_code} - Type: {status.endpoint_type}"
          )

    self.endpoints = results

async def main_async(config_path: str):
  checker = EndpointChecker(config_path)
  await checker.check_all_endpoints()
  checker.report_problems()

def main(config_path: str):
  asyncio.run(main_async(config_path))

if __name__ == "__main__":
  import sys
  if len(sys.argv) != 2:
    print("Usage: python endpoints_status.py <config_file>")
    sys.exit(1)

  main(sys.argv[1])
