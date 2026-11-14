// Safety screen shown once, before anything else in the app.
// Text is carried over verbatim from the original build.

export const DISCLAIMER_VERSION = '2026-09-07';
export const DISCLAIMER_TITLE = 'Before you train';

export type DisclaimerItem = { heading: string; body: string };

export const DISCLAIMER_ITEMS: DisclaimerItem[] = [
  {
    heading: 'This is not medical advice',
    body: 'Court Craft gives general training suggestions. It is not a doctor, a physio, or a coach who can see you, and nothing in it is medical advice.',
  },
  {
    heading: 'Check with a doctor first',
    body: 'Talk to a doctor before starting any new training, especially if you have an injury, a health condition, or have been away from sport for a while.',
  },
  {
    heading: 'Stop if something hurts',
    body: 'Sharp pain, dizziness, chest pain or shortness of breath means stop straight away and get medical help. Sore is normal. Pain is not.',
  },
  {
    heading: 'Under 18? Bring an adult in',
    body: 'If you are under 18, go through your plan with a parent, guardian or coach before you start, and train where an adult can see you.',
  },
  {
    heading: 'You train at your own risk',
    body: 'Basketball and strength training carry a real risk of injury. You choose what to attempt, and you are responsible for training within your ability and stopping when you should.',
  },
];

export const WARRANTY_SUMMARY =
  'Court Craft is provided as is, without warranty of any kind. To the fullest extent the law allows, the developer is not liable for any injury, loss or damage arising from your use of the app. If your local law does not allow some of these limits, they apply only as far as it does.';

export const PRIVACY_SUMMARY =
  'Court Craft keeps everything on your phone. Your name, answers, workouts and scores never leave the device, are never sent to a server, and are never shared or sold. There are no accounts, no tracking and no advertising. Deleting the app deletes the data with it.';
