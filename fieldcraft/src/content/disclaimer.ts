// Safety screen shown once, before anything else in the app.
// Football carries contact and heat risks that basketball does not, so this
// is stricter than the Court Craft version it is modelled on.

export const DISCLAIMER_VERSION = '2026-09-09';
export const DISCLAIMER_TITLE = 'Before you train';

export type DisclaimerItem = { heading: string; body: string };

export const DISCLAIMER_ITEMS: DisclaimerItem[] = [
  {
    heading: 'This is not medical advice',
    body: 'Fieldcraft gives general training suggestions. It is not a doctor, an athletic trainer, or a coach who can see you, and nothing in it is medical advice.',
  },
  {
    heading: 'Check with a doctor first',
    body: 'Talk to a doctor before starting any new training, especially if you have an injury, a health condition, or have been away from the sport for a while.',
  },
  {
    heading: 'No live contact on your own',
    body: 'Every contact drill here is form work only, done at walking or jogging speed with no one to hit. Live tackling, blocking and full-speed collisions belong in supervised practice, in full pads, with a coach present. Never run them alone or with friends in a backyard.',
  },
  {
    heading: 'Head injuries are different',
    body: 'If you take a blow to the head and feel dazed, sick, foggy, or your head hurts, stop for the day and tell an adult. Do not train again until a medical professional clears you. Never try to push through a suspected concussion.',
  },
  {
    heading: 'Heat is the danger nobody plans for',
    body: 'Football training happens in the heat. Drink before you are thirsty, take real breaks in shade, and build up gradually in the first two weeks. Dizziness, chills, confusion, a pounding headache or a stop in sweating means stop immediately and get help.',
  },
  {
    heading: 'Stop if something hurts',
    body: 'Sharp pain, chest pain, numbness, a joint that gives way, or shortness of breath means stop straight away and get medical help. Sore is normal. Pain is not.',
  },
  {
    heading: 'Under 18? Bring an adult in',
    body: 'If you are under 18, go through your plan with a parent, guardian or coach before you start, and train where an adult can see you.',
  },
  {
    heading: 'You train at your own risk',
    body: 'Football and strength training carry a real risk of serious injury. You choose what to attempt, and you are responsible for training within your ability, using safe ground and equipment, and stopping when you should.',
  },
];

export const WARRANTY_SUMMARY =
  'Fieldcraft is provided as is, without warranty of any kind. To the fullest extent the law allows, the developer is not liable for any injury, loss or damage arising from your use of the app. If your local law does not allow some of these limits, they apply only as far as it does.';

export const PRIVACY_SUMMARY =
  'Fieldcraft keeps everything on your phone. Your name, answers, workouts and scores never leave the device, are never sent to a server, and are never shared or sold. There are no accounts, no tracking and no advertising. Deleting the app deletes the data with it.';
