// Safety screen shown once, before anything else in the app.
// Hockey's specific risks are pucks at speed, sticks, and the ice itself.

export const DISCLAIMER_VERSION = '2026-09-15';
export const DISCLAIMER_TITLE = 'Before you train';

export type DisclaimerItem = { heading: string; body: string };

export const DISCLAIMER_ITEMS: DisclaimerItem[] = [
  {
    heading: 'This is not medical advice',
    body: 'Rinkcraft gives general training suggestions. It is not a doctor, an athletic trainer, or a coach who can see you, and nothing in it is medical advice.',
  },
  {
    heading: 'Check with a doctor first',
    body: 'Talk to a doctor before starting any new training, especially if you have an injury, a health condition, or have been away from the sport for a while.',
  },
  {
    heading: 'Never shoot where people are',
    body: 'A puck or ball off a stick can break bones and blind. Shoot only into a net or a backstop you have checked, with nobody in front of it or beside it, and never towards a window, a road or a garage door.',
  },
  {
    heading: 'Wear eye protection to shoot',
    body: 'Pucks bounce back off posts, boards and pads in ways you cannot predict. Wear a cage or visor for any shooting work, even in the driveway.',
  },
  {
    heading: 'Head injuries are different',
    body: 'If you take a blow to the head and feel dazed, sick, foggy, or your head hurts, stop for the day and tell an adult. Do not train again until a medical professional clears you. Never push through a suspected concussion.',
  },
  {
    heading: 'Ice work needs supervision',
    body: 'Everything here is built for off-ice training you can do alone. On-ice work belongs at a supervised rink session with a coach, in full equipment, never on a frozen pond or a rink you have let yourself into.',
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
    body: 'Hockey and strength training carry a real risk of serious injury. You choose what to attempt, and you are responsible for training within your ability, using safe ground and equipment, and stopping when you should.',
  },
];

export const WARRANTY_SUMMARY =
  'Rinkcraft is provided as is, without warranty of any kind. To the fullest extent the law allows, the developer is not liable for any injury, loss or damage arising from your use of the app. If your local law does not allow some of these limits, they apply only as far as it does.';

export const PRIVACY_SUMMARY =
  'Rinkcraft keeps everything on your phone. Your name, answers, workouts and scores never leave the device, are never sent to a server, and are never shared or sold. There are no accounts, no tracking and no advertising. Deleting the app deletes the data with it.';
