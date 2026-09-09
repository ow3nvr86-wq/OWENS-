# AI automation service — prospecting and delivery playbook

Companion to the sales site. Everything here is meant to be used in order:
build the list, make the calls, close a pilot, deliver it.

---

## 1. Building the call list

You do not buy a list. Bought lists are stale, over-called, and full of businesses
that closed. You build one in an afternoon from public records, and it will be better
than anything you could pay for.

### Source A — your state contractor licensing board (best source)

Almost every state runs a free, public, searchable database of licensed contractors.
Search for `[your state] contractor license lookup`. Filter by county or city.

Why this beats everything else:

- The business is verified real and currently licensed.
- Most records carry a business name, address, phone, and license class.
- License class tells you the trade before you dial.
- Issue date tells you how established they are. Look for licenses 5 to 20 years old.
  Under 5 years usually means no money yet. Over 25 often means the owner is winding down.

### Source B — Google Maps

Search each of these, in your city, then a 20 and 40 mile radius:

```
general contractor
roofing contractor
HVAC contractor
electrician
plumber
concrete contractor
remodeling contractor
excavation contractor
landscaping company
paving contractor
```

Read the listing before adding it to the list. You want:

| Signal | What you want | Why |
| --- | --- | --- |
| Google reviews | 15 to 150 | Enough to prove real volume, few enough that they still need more |
| Website | Exists, looks 2015 | Real business, no in-house marketing person |
| Photos | Owner-posted job photos | Someone is actually running the profile |
| Hours listed | Yes | Organized enough to buy something |
| "Responds quickly" badge | Missing | Direct evidence of the problem you fix |

Skip anything with a national franchise name. Corporate handles their software.

### Source C — trade associations and chambers

Member directories are public, and members are by definition the owners who
invest in their business rather than coasting.

- Your local Home Builders Association member list
- Associated Builders and Contractors, your state chapter
- Your city or county Chamber of Commerce directory
- Better Business Bureau, filtered by contractor categories

### Source D — permit records

Your county or city building department publishes issued permits, usually with the
contractor named on each one. A contractor pulling permits every week is busy, and busy
is the whole qualification. Search `[your county] building permits search`.

### The qualification bar

Add a business to the list only if all four are true:

1. Between 5 and 50 employees. Under 5 has no budget. Over 50 has staff for this.
2. Has a phone number that reaches the owner or the office, not a call center.
3. Actively working. Recent reviews, recent permits, or recent job photos.
4. Within driving distance. You want to be able to say "I'm local" and mean it.

Target: **120 qualified businesses** before you make the first call. That is roughly
one afternoon of work and it is enough to get three pilots.

### Tracking

One spreadsheet. Columns:

`Business | Trade | Owner name | Phone | City | Reviews | Source | Call 1 | Call 2 | Call 3 | Outcome | Notes`

Three columns for calls because the money is in the second and third attempt. Most
people quit after the first, which is exactly why the second one works.

---

## 2. The call

### When to call

Trades owners are unreachable 9am to 3pm. Call:

- **6:45am to 7:45am** — the best window by a wide margin. They are in the truck,
  driving to the first job, bored, and they answer their own phone.
- **4:30pm to 6:00pm** — off site, doing paperwork, in a bad mood about paperwork.

Never Monday morning. Never Friday afternoon.

### The opener

Do not lead with AI. The word makes trades owners hang up. Lead with the symptom.

> "Hey, is this [Name]? Good — I'll be quick, I know you're driving.
> I'm [Your Name], I'm local, out of [City]. I set up systems for contractors so the
> calls you miss while you're on a job get answered automatically.
> Quick question and then I'll let you go: how many calls do you figure you miss
> in a normal week?"

Then stop talking. The number they say is the entire sale. Everyone says a number
bigger than they expected to say, and hearing themselves say it does the work.

### The follow-up questions

Ask these in order. You are not pitching, you are taking notes.

1. "When you miss one, who calls them back, and when?"
2. "How many bids do you have sitting out right now with no answer?"
3. "What's an average job worth to you?"
4. "What are you using for scheduling and invoicing right now?"
5. "What's the part of the week you hate most?"

Question 5 is the one that sells. Whatever they answer is what you build first.

### The close

> "Here's what I'd do. Pick the one that's costing you the most — sounds like
> it's [the thing they said]. I build that one system, it's live in seven days,
> and it's $750 to build plus $300 a month to run it. If it isn't working in
> seven days you don't pay me the build fee.
> Can I send you a link and call you Thursday?"

Send the site. Call Thursday. Actually call Thursday.

### Expected numbers

Be realistic about this so you don't quit in week two.

| Stage | Rough rate | Out of 120 |
| --- | --- | --- |
| Reach a human | 25 to 35% | 30 to 42 |
| Real conversation | 40% of those | 12 to 17 |
| Agrees to a follow-up | 50% of those | 6 to 8 |
| Pays for a pilot | 35% of those | 2 to 3 |

Two or three pilots from 120 calls is a normal, healthy result. That is $1,500 to
$2,250 in build fees plus $600 to $900 a month recurring, from one afternoon of
list building and about eight hours on the phone.

The recurring is the real prize. Ten pilot clients is $3,000 a month before you
have upgraded a single one of them.

---

## 3. Pricing

| Tier | Build | Monthly | What's included |
| --- | --- | --- | --- |
| Pilot | $750 | $300 | One automation, live in 7 days |
| Operator | $2,400 | $600 | Three automations, wired into their job software, monthly report |
| Full desk | $5,000 | $1,100 | Whole catalog, custom work, business-hours phone access |

### Why these numbers

- **$750 is deliberately low.** It is under the threshold where a contractor needs
  to think about it, and it is roughly one job's profit. You are buying case studies
  with your first three clients, not maximizing revenue.
- **$300 a month is the real product.** It is less than they pay for one bad shared
  lead from a lead marketplace, and it never stops working.
- Raise the Pilot to $1,500 once you have three clients you can name.
- Never discount the monthly. Discount the build fee if you have to.

### Costs you carry

Per client, roughly:

- SMS and phone number: $10 to $30 a month depending on volume
- Automation platform seat: $10 to $30 a month
- Model API usage: $5 to $40 a month for this kind of workload

So on a $300 client you keep somewhere around $220 to $260. That margin is why this
business works at small scale.

---

## 4. What you are actually building

The website sells it. This is what happens after they pay.

### The stack

Do not write custom infrastructure for your first clients. Use:

- **Orchestration** — Make.com or n8n. Visual, fast to build, easy to hand over.
- **Phone and SMS** — Twilio, or OpenPhone if they want a real app for it.
- **Intelligence** — the Claude API for anything that has to read, summarize, or write.
- **Their existing tools** — Jobber, ServiceTitan, Buildertrend, Housecall Pro,
  QuickBooks. Never make them switch. Connecting to what they already have is
  most of your value.
- **Claude Code** — you use it to build and debug the glue, the price-book parsing,
  the report formatting. The client never sees it.

### Worked example: AUT-01, missed-call text back

The single best first build. Roughly four hours of work.

1. Port their existing business number to Twilio, or set call forwarding so
   unanswered calls hit a Twilio number after four rings.
2. On the missed-call webhook, fire an SMS from their number:
   *"Sorry we missed you — we're on a job site. Text me what you need and the address
   and I'll get right back to you. — [Owner], [Company]"*
3. Customer replies. Route the reply through the Claude API with a prompt that pulls
   out job type, address, urgency, and a one-line summary.
4. Push that summary into their job software as a new lead, and text the owner a
   single clean line: *"New lead — roof leak, 412 Oak St, says water is coming in
   now. Called at 2:14pm."*
5. If the owner doesn't respond in 30 minutes, text them again.

What you tell the client it does: *"You stop losing the ones who call once."*

### Worked example: AUT-03, voice note to estimate

The highest-value build, and the one that makes you hard to fire.

1. Get their price book. It will be a spreadsheet, a PDF, or in the owner's head.
   If it's in their head, spend an hour on the phone writing it down. That hour is
   the most valuable thing you will do for them.
2. Owner records a voice memo walking the job and sends it to a dedicated number.
3. Transcribe it, then pass the transcript plus their price book to the Claude API
   with instructions to produce line items, quantities, and prices, and to flag
   anything it wasn't sure about.
4. Render it into their estimate template and email the owner a draft to correct.
5. Never auto-send to the customer. The owner approves every estimate. Say this out
   loud on the sales call, because it is the objection they are about to raise.

### Build order across the catalog

Ship in this order. Each one is easier than the last because you already have
the plumbing from the one before.

1. AUT-01 missed-call text back — fastest payback, easiest sale
2. AUT-02 quote follow-up — same messaging pipes, new trigger
3. AUT-08 review requests — trivial once 1 and 2 exist
4. AUT-07 invoice chasing — needs their accounting connection
5. AUT-04 change orders — needs a document template
6. AUT-06 daily job reports — needs image handling
7. AUT-03 voice note to estimate — needs the price book, worth the effort
8. AUT-05 compliance document tracking — needs a real data store

### Rules that keep you out of trouble

- **Nothing goes to a customer without the owner having approved the wording once.**
- **Log every message you send on their behalf.** When something goes wrong, and it
  will, you need to be able to show exactly what happened.
- **Never touch their money.** Read invoice balances, send reminders, do not process
  payments. That is a different business with a different regulatory surface.
- **Get the automation rules in writing** before you build. One page, what fires,
  when, and what it says. Signed. This prevents the entire category of argument
  where they say they never agreed to a system texting their customers.

---

## 5. First 30 days

| Days | Do this |
| --- | --- |
| 1 to 2 | Replace every `[[ ]]` placeholder on the site. Get a phone number. Pick a real business name and check your state's registry. |
| 3 | Build the list of 120. State license board first, Google Maps second. |
| 4 to 8 | Call 25 a day in the 6:45am window. Log every one. |
| 9 to 12 | Second attempt on everyone you didn't reach. This is where the pilots come from. |
| 13 to 20 | Build the first pilot. AUT-01. Get it live. |
| 21 to 30 | Watch it run, fix the wording, then ask that client for one referral and one written sentence you can put on the site. |

The referral is worth more than the next 120 calls. Ask for it out loud, on the
phone, once the system has caught its first real lead. That is the moment.

---

## Open item

The call list in section 1 is a method, not names. To turn it into an actual
list of businesses with phone numbers, the city or county has to be filled in.
