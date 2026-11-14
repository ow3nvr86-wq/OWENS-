// Safety screen shown once, before anything else in the app.
// Volleyball's specific risks are jumping volume, shoulders and fingers.

export const DISCLAIMER_VERSION = '2026-09-15';
export const DISCLAIMER_TITLE = 'Before you train';

export type DisclaimerItem = { heading: string; body: string };

export const DISCLAIMER_ITEMS: DisclaimerItem[] = [
  {
    heading: 'This is not medical advice',
    body: 'Rallycraft gives general training suggestions. It is not a doctor, a physio, or a coach who can see you, and nothing in it is medical advice.',
  },
  {
    heading: 'Check with a doctor first',
    body: 'Talk to a doctor before starting any new training, especially if you have an injury, a health condition, or have been away from the sport for a while.',
  },
  {
    heading: 'Jumping adds up fast',
    body: 'Most volleyball injuries come from landing, not from one bad moment. Build jump volume gradually, land on two feet with bent knees, and take a full day off jumping when your knees ache.',
  },
  {
    heading: 'Look after your hitting shoulder',
    body: 'Hitting and serving load the same shoulder over and over. If it aches at rest, hurts when you reach overhead, or feels weak, stop swinging and get it looked at before it becomes a long injury.',
  },
  {
    heading: 'Fingers and ankles',
    body: 'Tape or brace if you have a history of sprains, warm your hands up before you block or set hard, and never play on an ankle that gave way until it has been checked.',
  },
  {
    heading: 'Stop if something hurts',
    body: 'Sharp pain, a joint that gives way, numbness, dizziness or chest pain means stop straight away and get medical help. Sore is normal. Pain is not.',
  },
  {
    heading: 'Under 18? Bring an adult in',
    body: 'If you are under 18, go through your plan with a parent, guardian or coach before you start, and train where an adult can see you.',
  },
  {
    heading: 'You train at your own risk',
    body: 'Volleyball and strength training carry a real risk of injury. You choose what to attempt, and you are responsible for training within your ability, using safe ground and equipment, and stopping when you should.',
  },
];

export const WARRANTY_SUMMARY =
  'Rallycraft is provided as is, without warranty of any kind. To the fullest extent the law allows, the developer is not liable for any injury, loss or damage arising from your use of the app. If your local law does not allow some of these limits, they apply only as far as it does.';

export const PRIVACY_SUMMARY =
  'Rallycraft keeps everything on your phone. Your name, answers, workouts and scores never leave the device, are never sent to a server, and are never shared or sold. There are no accounts, no tracking and no advertising. Deleting the app deletes the data with it.';
