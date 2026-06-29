const BASE = import.meta.env.BASE_URL

export function asset(path) {
  if (!path.startsWith('/')) path = '/' + path
  return BASE === '/' ? path : BASE.replace(/\/$/, '') + path
}

export { BASE }
