// One list row: "[x] Title <url>" for read items, "[ ] Title <url>" otherwise.
export function formatItem(item) {
  var mark = item.read ? "x" : " ";
  var text = "[" + mark + "] " + item.title;
  if (item.url) text = text + " <" + item.url + ">";
  return text;
}
