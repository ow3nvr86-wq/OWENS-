# Setup checklist

Two separate setups. Part A you do once, for yourself. Part B you repeat for
every client. Do them in order and don't skip ahead.

**Definition, so it's written down somewhere:** an automation is an
if-this-then-that rule a computer follows by itself, forever, with nobody
watching. A motion sensor light is an automation. Yours is: *if a call goes
unanswered, then text that caller back.*

---

## Part A — your own setup, one time

### A1. Sort the age problem first

- [ ] Confirm who holds the accounts

Twilio, Stripe, and Make.com all require the account holder to be 18 or over.
Same wall as the Apple Developer Program. If that's you, a parent or guardian
opens the accounts in their name and you do the work under them. Settle this
before you spend a week building, because every step below depends on it.

### A2. Accounts

- [ ] **Twilio** account created — twilio.com. Free to open, needs a card.
      This is what owns a phone number and can tell when a call went unanswered.
- [ ] **Make.com** account created — free tier is plenty to start.
      This is the drag-and-drop website where you connect "when this happens"
      to "do that." No coding.
- [ ] **Google Voice** number for yourself — free. Keeps business calls off
      your personal cell.
- [ ] A way to get paid. Stripe eventually. For your first three clients a
      check or Zelle is completely fine.

You do **not** need an LLC to start. Sole proprietor is legal and free.
Register later, once money is actually coming in.

### A3. Register for A2P 10DLC — do this on day one

- [ ] Brand registered in Twilio
- [ ] Campaign registered in Twilio
- [ ] Approval received

**Read this part twice.** In the US, sending business texts through Twilio
requires registering what's called A2P 10DLC. It's a form in the Twilio
console describing your business and what your texts say. It costs a few
dollars and takes anywhere from a day to a couple of weeks to approve.

If you skip it, your texts get silently filtered by the carriers and never
arrive. Nothing errors. It just doesn't work, and you'll waste days trying to
figure out why. Start this on day one so it's approved by the time you have a
client.

### A4. Build it on your own number first

This is the step people skip and it's the most important one on this page.

- [ ] Bought a Twilio phone number
- [ ] Built the two-box scenario in Make (see Part B, step 4)
- [ ] Called the number from a friend's phone and let it ring out
- [ ] The text arrived
- [ ] Tested from a second phone on a different carrier
- [ ] Tested from a landline or blocked number, confirmed nothing breaks

Now you have a live demo. On a sales call you say *"do me a favor, call this
number right now and hang up."* Four seconds later his phone buzzes. That
demo closes deals that no explanation will.

### A5. Before you dial anybody

- [ ] Replaced all four `[[ ]]` placeholders in `business/site.html`
- [ ] Checked the business name isn't taken in your state's registry
- [ ] Site is live at a URL you can text to someone
- [ ] Built the list of 120 contractors (see the playbook, section 1)
- [ ] Spreadsheet ready with three columns for call attempts

---

## Part B — setting up one client

Roughly five hours of real work, spread across a few days.

### B1. Collect four things from the owner

- [ ] Their business phone number
- [ ] Their personal cell, where the alerts go
- [ ] Their working hours
- [ ] **How they'd word the text, in their own words**

On the last one: ask him to say it out loud and write down exactly what he
says. Do not clean it up. If he says "we're out on a job," do not turn that
into "we are currently unavailable." The whole point is that it sounds like
him.

- [ ] Got the automation rules signed on one page: what fires, when, and
      exactly what it says

That signature prevents the entire category of argument where he later says
he never agreed to a system texting his customers.

### B2. Point missed calls at Twilio

- [ ] Conditional call forwarding turned on, on the owner's phone

**Do not port their number.** Porting means moving the number to Twilio
permanently. It takes days and if it goes wrong their business phone is dead
and it's your fault.

Instead use conditional call forwarding, a feature their carrier already has.
It means "if I don't answer after five rings, send the call here." Their
number stays exactly where it is, and if you unplug everything tomorrow their
phone goes back to normal on its own.

The dial code is different on every carrier. Search
`[their carrier] conditional call forwarding no answer`, or call the carrier
and ask. On many GSM carriers it's a `**61*` code; Verizon often uses `*71`.
Confirm it for their specific carrier rather than guessing.

Have the **owner** dial the code on his own phone while you're on the line
with him. Don't do it for him.

### B3. Set up the Twilio number

- [ ] Bought a Twilio number for this client
- [ ] Forwarding from B2 points at it
- [ ] Client added to your approved A2P campaign

### B4. Wire two boxes in Make

- [ ] Box one: a call came in and wasn't answered
- [ ] Box two: send this text to whoever called
- [ ] Text includes the owner's name and business name
- [ ] Text includes an opt-out line

That's genuinely it for version one. Two boxes.

The opt-out line matters. Something like "Reply STOP to opt out." Twilio
handles STOP automatically once it's there, and it keeps you on the right side
of texting rules.

### B5. Route the reply to the owner

- [ ] When the customer texts back, that text lands on the owner's cell

For your first client, just forward it plainly. Running it through Claude to
summarize it into a tidy one-liner is a nice upgrade for month two. Don't
fight that on day one.

### B6. Test three times before he ever sees it

- [ ] Called from your phone, let it ring out, text arrived
- [ ] Called from a friend's phone on a different carrier, text arrived
- [ ] Called and actually answered — confirmed no text goes out
- [ ] Texted STOP, confirmed it stops

That third test matters. If the system texts people he *did* answer, he'll
kill it the same day.

### B7. Hand it over

- [ ] Fifteen minutes on the phone showing him it working
- [ ] He has your cell number
- [ ] He knows to text you the second anything sounds wrong

Then answer when he texts. Same day. That responsiveness is most of what the
monthly fee actually buys.

### B8. Watch it for two weeks

- [ ] Checked daily that texts are going out
- [ ] Fixed the wording at least once, because there's always something
- [ ] Asked, once the system catches its first real lead, for a referral and
      one written sentence you can put on the site

Ask for the referral out loud, on the phone, in the moment he's happy. That
moment is worth more than the next 120 cold calls.

---

## The order that actually matters

1. Sort out who holds the accounts
2. Start the A2P registration, because it's the slow one
3. Build it on your own number
4. Then start calling

Everything else can be figured out as you go. Those four in that order.
