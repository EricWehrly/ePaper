/**
 * Utility functions for the ePaper web interface
 */

/**
 * Fetch and parse JSON from a URL
 * @param {string} path - URL path to fetch
 * @returns {Promise<object>} Parsed JSON response
 */
export async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Network error');
  return res.json();
}

/**
 * Create a DOM element with attributes and children
 * @param {string} tag - HTML tag name
 * @param {object} attrs - Element attributes
 * @param {...(string|Element)} children - Child elements or text
 * @returns {Element} Created element
 */
export function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v;
    else e.setAttribute(k, v);
  });
  children.forEach(c => {
    if (typeof c === 'string') e.appendChild(document.createTextNode(c));
    else e.appendChild(c);
  });
  return e;
}
