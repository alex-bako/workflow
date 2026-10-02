// Shared clock helpers, used by reminders and snooze.
export const now = () => new Date();

export function addSeconds(date, seconds) {
  return new Date(date.getTime() + seconds);
}
