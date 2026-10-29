/**
 * Creates a shader of the given type from the provided source code.
 *
 * @param {WebGL2RenderingContext} gl - The WebGL context.
 * @param {number} type - The shader type (gl.VERTEX_SHADER or gl.FRAGMENT_SHADER).
 * @param {string} source - The shader source code as a string.
 * @returns {WebGLShader|null} - The compiled shader object, or null if compilation failed.
 */
export function createShader(gl, type, source) {
  const shader = gl.createShader(type);
  if (!shader) {
    console.error('Failed to create shader object.');
    return null;
  }

  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const errorLog = gl.getShaderInfoLog(shader);
    console.error(`Shader compilation failed: ${errorLog}`);
    gl.deleteShader(shader);
    return null;
  }

  return shader;
}