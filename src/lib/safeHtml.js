const ALLOW = new Set(['P', 'B', 'STRONG', 'EM', 'BR', 'SPAN'])

export function sanitize(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, 'text/html')
  const walk = (node) => {
    ;[...node.childNodes].forEach((child) => {
      if (child.nodeType === 1) {
        if (!ALLOW.has(child.tagName)) {
          const parent = child.parentNode
          while (child.firstChild) parent.insertBefore(child.firstChild, child)
          parent.removeChild(child)
        } else {
          ;[...child.attributes].forEach((a) => child.removeAttribute(a.name))
          walk(child)
        }
      } else if (child.nodeType === 8) {
        child.remove()
      }
    })
  }
  walk(doc.body)
  return doc.body.innerHTML
}
