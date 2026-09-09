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
      { value: 'QB', label: 'Quarterback' },
      { value: 'RB', label: 'Running Back' },
      { value: 'WR', label: 'Wide Receiver' },
      { value: 'TE', label: 'Tight End' },
      { value: 'OL', label: 'Offensive Line' },
      { value: 'DL', label: 'Defensive Line' },
      { value: 'LB', label: 'Linebacker' },
      { value: 'DB', label: 'Cornerback or Safety' },
      { value: 'K', label: 'Kicker or Punter' },
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
      { value: 'speed', label: 'Speed' },
      { value: 'agility', label: 'Agility and Change of Direction' },
      { value: 'power', label: 'Strength and Power' },
      { value: 'hands', label: 'Catching and Ball Security' },
      { value: 'routes', label: 'Route Running' },
      { value: 'throwing', label: 'Throwing' },
      { value: 'blocking', label: 'Blocking and Tackling Form' },
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
      { value: 'none', label: 'Just open space', hint: 'No ball needed' },
      { value: 'ball', label: 'A ball and space', hint: 'Yard or park' },
      { value: 'cones', label: 'Cones and a field' },
      { value: 'gym', label: 'Field and a weight room' },
    ],
  },
];
