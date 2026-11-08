# Delegation Boundary

| # | Action | Decision | Justification |
|---|--------|----------|---------------|
| 1 | Read the appointments of a day | alone | Only reads my own data; nothing changes. |
| 2 | Look up the weather | alone | Only reads public data; no side effects. |
| 3 | Search train connections | alone | Only reads; searching costs nothing and commits me to nothing. |
| 4 | Read notes | alone | Only reads my own data; nothing leaves me. |
| 5 | Create a personal block in the calendar | alone | Affects only my calendar, notifies no one, easy to delete. |
| 6 | Reschedule an appointment with other attendees | approval | Other people are notified and have to adjust their plans. |
| 7 | Book a train ticket | approval | Costs money and may not be refundable. |
| 8 | Send a message to third parties | approval | Speaks in my name and cannot be unsent. |
| 9 | Create a note | alone | Only adds to my own data; easy to delete. |
| 10 | Delete a note | approval | Cannot be undone, and the agent can't know which notes still matter. |

## Rule

The agent acts alone unless an action costs money, reaches other people, or cannot be undone.

## Observations

1. The agent sometimes acted without asking, even where a question would have been appropriate.
2. At other times the agent was too careful and asked questions that were unnecessary.
