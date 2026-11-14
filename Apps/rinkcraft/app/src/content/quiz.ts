// The seven-step setup flow. Same shape as Court Craft, football answers.

export type QuizOption = {
  value: string | number;
  label: string;
  hint?: string;
};

export type QuizStep = {
  key: string;
  prompt: string;
  label?: string;
  input?: 'text';
  placeholder?: string;
  multi?: boolean;
  hint?: string;
  options: QuizOption[];
};

export const QUIZ: QuizStep[] = [
  {
    key: 'name',
    prompt: 'What should we call you?',
    input: 'text',
    placeholder: 'First name',
    options: [],
  },
  {
    key: 'positions',
    prompt: 'What position do you play?',
    label: 'Position',
    multi: true,
    hint: 'Pick every position you play.',
    options: [
      { value: 'C', label: 'Centre' },
      { value: 'W', label: 'Winger' },
      { value: 'D', label: 'Defence' },
      { value: 'G', label: 'Goaltender' },
    ],
  },
  {
    key: 'level',
    prompt: 'What level are you playing?',
    label: 'Level',
    options: [
      { value: 'youth', label: 'Youth league', hint: '12 and under' },
      { value: 'middle', label: 'Middle School', hint: '13 and up' },
      { value: 'high', label: 'High School' },
      { value: 'college', label: 'College or above' },
    ],
  },
  {
    key: 'focus',
    prompt: 'What do you want to improve?',
    label: 'Focus',
    multi: true,
    hint: 'Pick one for a deep session, or several to split your time.',
    options: [
      { value: 'stickhandling', label: 'Stickhandling' },
      { value: 'shooting', label: 'Shooting' },
      { value: 'passing', label: 'Passing' },
      { value: 'skating', label: 'Skating and Edges' },
      { value: 'agility', label: 'Agility and Footwork' },
      { value: 'power', label: 'Strength and Power' },
      { value: 'goalie', label: 'Goaltending' },
      { value: 'conditioning', label: 'Conditioning' },
    ],
  },
  {
    key: 'daysPerWeek',
    prompt: 'How many days a week can you train?',
    label: 'Days a week',
    options: [
      { value: 2, label: '2 days' },
      { value: 3, label: '3 days' },
      { value: 4, label: '4 days' },
      { value: 5, label: '5 days' },
      { value: 6, label: '6 days', hint: 'One full rest day' },
      { value: 7, label: '7 days', hint: 'Every day, no rest day' },
    ],
  },
  {
    key: 'sessionMinutes',
    prompt: 'How long is one session?',
    label: 'Session length',
    options: [
      { value: 20, label: '20 minutes' },
      { value: 30, label: '30 minutes' },
      { value: 45, label: '45 minutes' },
      { value: 60, label: '60+ minutes' },
    ],
  },
  {
    key: 'equipment',
    prompt: 'What do you have access to?',
    label: 'Equipment',
    options: [
      { value: 'none', label: 'Just open space', hint: 'No stick needed' },
      { value: 'stick', label: 'Stick and a ball', hint: 'Driveway or garage' },
      { value: 'pad', label: 'Shooting pad and a net' },
      { value: 'ice', label: 'Ice time at a rink' },
      { value: 'gym', label: 'Rink and a weight room' },
    ],
  },
];
