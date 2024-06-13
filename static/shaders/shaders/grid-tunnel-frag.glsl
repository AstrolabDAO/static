#define PI 3.141592653589793
#define TAU 6.283185307179586

precision highp float;

uniform vec2 iResolution;
uniform vec2 iMouse;
uniform float iTime;
uniform float computedTime;
uniform float lineWidth;

// from iq / bookofshaders
float cubicPulse(float c, float w, float x) {
    x = abs(x - c);
    if (x > w)
        return 0.0;
    x /= w;
    return 1.0 - x * x * (3.0 - 2.0 * x);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Slow down the rotation speed by decreasing the time multiplier
    // float time = iTime * speed;

    // Create tunnel coordinates (p) and remap to normal coordinates (uv)
    // Technique from @iq: https://www.shadertoy.com/view/Ms2SWW
    // and a derivative:   https://www.shadertoy.com/view/Xd2SWD
    vec2 p = (-iResolution.xy + 2.0 * fragCoord) / iResolution.y; // normalized coordinates (-1 to 1 vertically)
    vec2 uvOrig = p;
    // added twist by me ------------
    float rotZ = 1. - 0.23 * sin(1.2 * cos(length(p * 1.5))); // Further slow down rotation by adjusting the sin and cos multipliers
    p *= mat2(cos(rotZ), sin(rotZ), -sin(rotZ), cos(rotZ));

    float a = atan(p.y, p.x); // angle of each pixel to the center of the screen
    float rSquare = pow(pow(p.x * p.x, 4.0) + pow(p.y * p.y, 4.0), 1.0 / 8.0); // modified distance metric
    float rRound = length(p);
    float r = mix(rSquare, rRound, 0.5 + 0.5 * sin(computedTime * 2.)); // interp between round & rect tunnels
    vec2 uv = vec2(.6 / r + computedTime, a / PI); // index texture by (animated inverse) radius and angle

    // subdivide to grid
    uv += vec2(0., 0.25 * sin(computedTime + uv.x * 1.2)); // pre-warp
    uv /= vec2(1. + 0.0002 * length(uvOrig));
    vec2 uvDraw = fract(uv * 12.); // create grid

    // draw lines (adjust lineWidth as needed for thinner strokes)
    float col = cubicPulse(0.5, lineWidth, uvDraw.x);
    col = max(col, cubicPulse(0.5, lineWidth * .85, uvDraw.y));

    // Uniform grid color defined
    vec3 gridColor = vec3(0.0, .2, .55); // Cyan, consistent across the grid

    // Background color - adjust as needed to darken/lighten the background
    vec3 backgroundColor = vec3(0.05, 0.05, 0.1); // Dark blue background

    // Fading effect: adjust alpha based on distance
    // Smaller 'fadeFactor' value will make the fading more pronounced
    float fadeFactor = 0.5; // Adjust this value to control the fade effect
    float alpha = smoothstep(0.0, fadeFactor, r);

    // Final color: Apply fading based on alpha -> mix grid color with background color based on fade value
    fragColor = vec4(mix(backgroundColor, gridColor, col * alpha), 1.0);
}

void main() {
    mainImage(gl_FragColor, gl_FragCoord.xy);
}
