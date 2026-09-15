// Safety screen shown once, before anything else in the app.
// The risks here are thrown and batted balls, and arm overuse.

export const DISCLAIMER_VERSION = '2026-09-15';
export const DISCLAIMER_TITLE = 'Before you train';

export type DisclaimerItem = { heading: string; body: string };

export const DISCLAIMER_ITEMS: DisclaimerItem[] = [
  {
    heading: 'This is not medical advice',
    body: 'Diamondcraft gives general training suggestions. It is not a doctor, an athletic trainer, or a coach who can see you, and nothing in it is medical advice.',
  },
  {
    heading: 'Check with a doctor first',
    body: 'Talk to a doctor before starting any new training, especially if you have an injury, a health condition, or have been away from the sport for a while.',
  },
  {
    heading: 'Your arm has a limit',
    body: 'Most serious arm injuries in this sport come from throwing too much, too hard, too often. Follow your league or coach pitch counts, take real rest days, and never pitch through elbow or shoulder pain. An arm that hurts is an arm asking you to stop.',
  },
  {
    heading: 'Never throw or hit where people are',
    body: 'A ball off a bat can kill. Check behind and beside your net every single time, never swing where anyone could walk, and never use a wall that faces a street, a window or a door.',
  },
  {
    heading: 'Wear a helmet and use a screen',
    body: 'Wear a helmet for live hitting and baserunning. Use a net or screen for any hitting into a target, and check it for holes before you start.',
  },
  {
    heading: 'Stop if something hurts',
    body: 'Sharp pain, a joint that gives way, numbness in your hand, dizziness or chest pain means stop straight away and get medical help. Sore is normal. Pain is not.',
  },
  {
    heading: 'Under 18? Bring an adult in',
    body: 'If you are under 18, go through your plan with a parent, guardian or coach before you start, and train where an adult can see you.',
  },
  {
    heading: 'You train at your own risk',
    body: 'Baseball, softball and strength training carry a real risk of injury. You choose what to attempt, and you are responsible for training within your ability, using safe ground and equipment, and stopping when you should.',
  },
];

export const WARRANTY_SUMMARY =
  'Diamondcraft is provided as is, without warranty of any kind. To the fullest extent the law allows, the developer is not liable for any injury, loss or damage arising from your use of the app. If your local law does not allow some of these limits, they apply only as far as it does.';

export const PRIVACY_SUMMARY =
  'Diamondcraft keeps everything on your phone. Your name, answers, workouts and scores never leave the device, are never sent to a server, and are never shared or sold. There are no accounts, no tracking and no advertising. Deleting the app deletes the data with it.';
