/**
 * Lightweight Markdown-to-HTML renderer.
 * Handles: **bold**, *italic*, `inline code`, line breaks, paragraphs.
 * Does NOT handle: headings, lists, links, images, tables (not needed for AI responses).
 */
export function renderMarkdown(text) {
  if (!text) return ''
  let html = text

  // Escape HTML first (but preserve entities already present)
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // Inline code: `code` (must be before bold/italic to avoid conflicts)
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // Bold: **text** or __text__
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>')

  // Italic: *text* or _text_ (but not inside words or bullets)
  html = html.replace(/(^|[^*\w])\*([^*\n]+)\*([^*\w]|$)/g, '$1<em>$2</em>$3')
  html = html.replace(/(^|[^_\w])_([^_\n]+)_([^_\w]|$)/g, '$1<em>$2</em>$3')

  // Double newlines → paragraph breaks
  html = html.replace(/\n\n+/g, '</p><p>')
  // Single newlines → <br>
  html = html.replace(/\n/g, '<br>')

  // Wrap in paragraph
  html = '<p>' + html + '</p>'

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '')
  // Clean up <br> before </p>
  html = html.replace(/<br>\s*<\/p>/g, '</p>')

  return html
}
