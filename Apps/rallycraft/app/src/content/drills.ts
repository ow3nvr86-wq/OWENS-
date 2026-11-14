// Rallycraft drill library.
//
// Written to be run alone. equipment is the MINIMUM needed:
//   none -> open space      ball -> a ball and space
//   wall -> a ball and a wall    net -> a net and a court
//   gym  -> court plus a weight room

export type Focus =
  | 'passing' | 'setting' | 'hitting' | 'serving'
  | 'blocking' | 'defense' | 'jumping' | 'conditioning';

export type Equipment = 'none' | 'ball' | 'wall' | 'net' | 'gym';

export type Drill = {
  id: string;
  name: string;
  focus: Focus;
  equipment: Equipment;
  positions: string[];
  work: string;
  setup?: string;
  how: string[];
  cue: string;
};

export const DRILLS: Drill[] = [
  // -------------------------------------------------------------- passing
  {
    id: 'platform-hold', name: 'Platform Hold', focus: 'passing', equipment: 'none',
    positions: ['all'], work: '3 rounds of 30 seconds',
    how: [
      'Stand in a low passing stance, feet wider than your shoulders, weight forward.',
      'Join your hands and lock your elbows so your forearms make one flat platform.',
      'Hold it still and check the platform stays level and away from your body.',
    ],
    cue: 'Elbows locked, thumbs level, shoulders in front of your knees.',
  },
  {
    id: 'wall-pass', name: 'Wall Passing', focus: 'passing', equipment: 'wall',
    positions: ['all'], work: '4 rounds of 25 passes',
    setup: 'Stand about two metres from a flat wall.',
    how: [
      'Toss the ball into the wall and pass the rebound straight back.',
      'Keep the ball off your hands and on the forearms every time.',
      'Move your feet to get behind it rather than reaching sideways.',
    ],
    cue: 'Angle the platform, do not swing at the ball.',
  },
  {
    id: 'pass-to-target', name: 'Pass to a Target', focus: 'passing', equipment: 'wall',
    positions: ['all'], work: '4 rounds of 20',
    setup: 'Mark a spot high on the wall as your setter.',
    how: [
      'Pass off the wall and aim every ball at the mark.',
      'Count how many in twenty hit within a body width of it.',
      'Try to beat that count next round.',
    ],
    cue: 'The platform points where the ball goes.',
  },
  {
    id: 'shuffle-pass', name: 'Shuffle and Pass', focus: 'passing', equipment: 'wall',
    positions: ['L', 'DS', 'OH'], work: '3 rounds of 16',
    how: [
      'Start two steps to one side of your wall target.',
      'Shuffle across, stop with both feet planted, then pass.',
      'Alternate sides and never pass while still moving.',
    ],
    cue: 'Feet stop before the ball arrives, always.',
  },
  {
    id: 'low-pass', name: 'Low Ball Pass', focus: 'passing', equipment: 'wall',
    positions: ['L', 'DS'], work: '3 rounds of 15',
    how: [
      'Throw the ball low into the base of the wall.',
      'Drop your hips to get under the rebound rather than bending at the waist.',
      'Pass it up high and soft.',
    ],
    cue: 'Bend the knees, not the back.',
  },
  {
    id: 'serve-receive-read', name: 'Serve Receive Read', focus: 'passing', equipment: 'net',
    positions: ['OH', 'L', 'DS'], work: '3 rounds of 12',
    setup: 'Have someone serve, or serve into the wall and receive the rebound.',
    how: [
      'Start in your receive stance and watch the server, not the ball.',
      'Move the moment you read the direction, then stop and pass.',
      'Reset to your start position between every ball.',
    ],
    cue: 'Read early, move early, then be still.',
  },
  {
    id: 'one-arm-dig', name: 'One Arm Pass', focus: 'passing', equipment: 'wall',
    positions: ['L', 'DS'], work: '3 rounds of 10 each arm',
    how: [
      'Throw the ball wide of yourself against the wall.',
      'Reach out and play the rebound with one forearm only.',
      'Keep the arm firm and angle it up.',
    ],
    cue: 'Firm arm, soft shoulder, aim high.',
  },

  // -------------------------------------------------------------- setting
  {
    id: 'hand-shape', name: 'Hand Shape Hold', focus: 'setting', equipment: 'ball',
    positions: ['S'], work: '3 rounds of 30 seconds',
    how: [
      'Hold the ball above your forehead with both hands in a wide triangle.',
      'Thumbs point at your eyes, fingers spread around the ball, wrists back.',
      'Hold still and check your elbows stay out, not tucked in.',
    ],
    cue: 'Make a window and look through it.',
  },
  {
    id: 'set-to-self', name: 'Setting to Yourself', focus: 'setting', equipment: 'ball',
    positions: ['all'], work: '4 rounds of 30 touches',
    how: [
      'Set the ball straight up, just above your head.',
      'Move your feet so it comes back down to your forehead every time.',
      'Keep the contact quiet and use your legs, not just your arms.',
    ],
    cue: 'Get under it. Never reach for it.',
  },
  {
    id: 'wall-set', name: 'Wall Setting', focus: 'setting', equipment: 'wall',
    positions: ['S', 'OH'], work: '4 rounds of 25',
    how: [
      'Set the ball into the wall above your head height and set the rebound back.',
      'Keep your hands high and finish with your arms extended at the target.',
      'Do not let the ball drop below your eyes.',
    ],
    cue: 'Finish long. Push it, do not slap it.',
  },
  {
    id: 'set-high-low', name: 'High Set, Low Set', focus: 'setting', equipment: 'ball',
    positions: ['S'], work: '3 rounds of 20',
    how: [
      'Alternate one set as high as you can with one that barely leaves your hands.',
      'Keep the hand shape identical for both.',
      'Control where each one lands.',
    ],
    cue: 'Same hands, different legs.',
  },
  {
    id: 'back-set', name: 'Back Setting', focus: 'setting', equipment: 'ball',
    positions: ['S'], work: '3 rounds of 15',
    how: [
      'Set the ball up, get under it, and push it back over your own head.',
      'Arch slightly and finish with your hands behind you.',
      'Turn and watch where it lands.',
    ],
    cue: 'Hips forward, hands through, eyes up.',
  },
  {
    id: 'jump-set', name: 'Jump Set', focus: 'setting', equipment: 'ball',
    positions: ['S'], work: '3 rounds of 12',
    how: [
      'Toss the ball up, jump straight, and set it at the top of the jump.',
      'Land balanced on both feet.',
      'Keep the set quiet and controlled rather than long.',
    ],
    cue: 'Set at the top, not on the way up.',
  },
  {
    id: 'set-footwork', name: 'Setter Footwork', focus: 'setting', equipment: 'none',
    positions: ['S'], work: '4 rounds of 8',
    setup: 'Mark a spot as the net and a spot as where you start.',
    how: [
      'Sprint from your defensive start to the setting spot.',
      'Arrive with the right foot last so you are square to the target.',
      'Freeze in your setting posture for one second, then reset.',
    ],
    cue: 'Right foot last, shoulders square.',
  },

  // -------------------------------------------------------------- hitting
  {
    id: 'arm-swing-shape', name: 'Arm Swing Shape', focus: 'hitting', equipment: 'none',
    positions: ['OH', 'OPP', 'MB'], work: '3 rounds of 15',
    how: [
      'Draw both elbows back high, hitting hand by your ear.',
      'Rotate your shoulders and swing fast and straight through the top of an imaginary ball.',
      'Finish with the hand past the opposite hip.',
    ],
    cue: 'Bow and arrow, then snap.',
  },
  {
    id: 'wall-hit', name: 'Wall Hitting', focus: 'hitting', equipment: 'wall',
    positions: ['OH', 'OPP', 'MB'], work: '4 rounds of 20',
    setup: 'Stand three metres from a wall with a high ceiling above you.',
    how: [
      'Toss the ball up and hit it down into the floor so it rebounds off the wall.',
      'Snap your wrist over the top of the ball.',
      'Catch the rebound and repeat.',
    ],
    cue: 'Hit the top of the ball, not the back.',
  },
  {
    id: 'approach-footwork', name: 'Four Step Approach', focus: 'hitting', equipment: 'none',
    positions: ['OH', 'OPP', 'MB'], work: '4 rounds of 8',
    how: [
      'Start well back. Take a small directional step, then a longer second step.',
      'Plant the last two steps quickly, heel first, arms swinging back behind you.',
      'Jump straight up and land on both feet.',
    ],
    cue: 'Slow, slow, quick quick. Arms back before you jump.',
  },
  {
    id: 'approach-jump', name: 'Approach and Reach', focus: 'hitting', equipment: 'none',
    positions: ['OH', 'OPP', 'MB'], work: '4 rounds of 6',
    setup: 'Pick a mark on a wall above your standing reach.',
    how: [
      'Run your full approach and jump, reaching as high as you can at the mark.',
      'Land softly on both feet with bent knees.',
      'Rest fully between reps so every jump is a real one.',
    ],
    cue: 'Every jump is maximum, or it is not worth doing.',
  },
  {
    id: 'tip-control', name: 'Tip and Roll Shot', focus: 'hitting', equipment: 'net',
    positions: ['OH', 'OPP', 'MB'], work: '3 rounds of 12',
    how: [
      'Approach and jump as if hitting hard.',
      'At the last moment, place the ball softly with stiff fingers instead of swinging.',
      'Aim for a target spot deep in the court.',
    ],
    cue: 'Same approach, different hand. Sell the swing.',
  },
  {
    id: 'hit-line-cross', name: 'Line and Cross', focus: 'hitting', equipment: 'net',
    positions: ['OH', 'OPP'], work: '3 rounds of 10 each direction',
    how: [
      'Approach the same way every time.',
      'Turn only your shoulders and hand to send the ball down the line, then crosscourt.',
      'Never change your feet to give the direction away.',
    ],
    cue: 'The feet lie, the hand tells the truth.',
  },
  {
    id: 'shoulder-care', name: 'Band Shoulder Set', focus: 'hitting', equipment: 'gym',
    positions: ['OH', 'OPP', 'MB', 'S'], work: '3 sets of 12 each way',
    how: [
      'With a light band, pull outward with the elbow tucked to your side.',
      'Then raise the arm to shoulder height and hold for two seconds.',
      'Keep it slow. This is protection, not strength work.',
    ],
    cue: 'Light band, slow tempo, no shrugging.',
  },

  // -------------------------------------------------------------- serving
  {
    id: 'toss-consistency', name: 'Toss Only', focus: 'serving', equipment: 'ball',
    positions: ['all'], work: '3 rounds of 20',
    how: [
      'Take your serving stance and toss the ball as if serving, but do not swing.',
      'Let it drop and see if it lands on the same spot each time.',
      'Mark that spot and try to hit it twenty times in a row.',
    ],
    cue: 'A bad toss is a bad serve before you even swing.',
  },
  {
    id: 'float-serve', name: 'Float Serve Contact', focus: 'serving', equipment: 'wall',
    positions: ['all'], work: '4 rounds of 15',
    how: [
      'Toss low and just in front of your hitting shoulder.',
      'Punch through the middle of the ball with a firm flat hand and stop the hand.',
      'No wrist snap at all, so the ball does not spin.',
    ],
    cue: 'Punch and freeze. Spin is the enemy here.',
  },
  {
    id: 'topspin-serve', name: 'Topspin Serve', focus: 'serving', equipment: 'wall',
    positions: ['all'], work: '4 rounds of 15',
    how: [
      'Toss higher and further in front, with a little spin on the toss.',
      'Swing fast and snap the wrist over the top of the ball.',
      'Follow through down past your hip.',
    ],
    cue: 'Snap over the top. Make it dive.',
  },
  {
    id: 'serve-zones', name: 'Serving Zones', focus: 'serving', equipment: 'net',
    positions: ['all'], work: '6 serves at each of 3 zones',
    setup: 'Mark three target areas on the far court.',
    how: [
      'Call the zone out loud before each serve.',
      'Serve to it and score a point for every hit.',
      'Write the score down and beat it next session.',
    ],
    cue: 'Never serve without picking a target first.',
  },
  {
    id: 'jump-serve-build', name: 'Jump Serve Build Up', focus: 'serving', equipment: 'net',
    positions: ['OH', 'OPP'], work: '3 rounds of 8',
    how: [
      'Start with a standing serve, then add one step, then the full approach.',
      'Only move up a stage when the toss stays consistent.',
      'Land on both feet inside the court.',
    ],
    cue: 'Earn each stage. The toss decides when.',
  },
  {
    id: 'pressure-serve', name: 'Pressure Serving', focus: 'serving', equipment: 'net',
    positions: ['all'], work: '10 serves',
    how: [
      'Give yourself a target of eight from ten in.',
      'If you miss three, start the set again.',
      'Serve at full match speed, not safe speed.',
    ],
    cue: 'Train the nerve, not just the technique.',
  },
  {
    id: 'serve-routine', name: 'Serve Routine', focus: 'serving', equipment: 'ball',
    positions: ['all'], work: '15 repetitions',
    how: [
      'Build a short routine: bounce, breath, target, toss, swing.',
      'Do exactly the same thing every single time.',
      'Say the routine out loud until it is automatic.',
    ],
    cue: 'Same routine under pressure as in the warm up.',
  },

  // ------------------------------------------------------------- blocking
  {
    id: 'block-hands', name: 'Block Hand Shape', focus: 'blocking', equipment: 'none',
    positions: ['MB', 'OH', 'OPP'], work: '3 rounds of 20 seconds',
    how: [
      'Stand with hands up in front of your shoulders, fingers spread wide and firm.',
      'Press them forward and slightly down, thumbs up.',
      'Hold and check your hands stay wider than your shoulders.',
    ],
    cue: 'Big hands, strong wrists, press over not up.',
  },
  {
    id: 'block-jump', name: 'Block Jump', focus: 'blocking', equipment: 'none',
    positions: ['MB', 'OH', 'OPP'], work: '4 rounds of 8',
    how: [
      'From a low ready stance, jump straight up with no dip of the arms.',
      'Press your hands over an imaginary net at the top.',
      'Land where you took off, on both feet.',
    ],
    cue: 'Arms stay up. No windmill.',
  },
  {
    id: 'block-shuffle', name: 'Blocker Shuffle', focus: 'blocking', equipment: 'none',
    positions: ['MB'], work: '4 rounds of 6 each way',
    setup: 'Mark three spots along an imaginary net, two metres apart.',
    how: [
      'Shuffle from the middle to one spot without crossing your feet.',
      'Square up, jump and press.',
      'Shuffle back and repeat the other way.',
    ],
    cue: 'Square to the net before you jump, never while you move.',
  },
  {
    id: 'block-crossover', name: 'Crossover Block Move', focus: 'blocking', equipment: 'none',
    positions: ['MB'], work: '4 rounds of 5 each way',
    how: [
      'Open your hips with a directional step, crossover, then plant both feet.',
      'Turn square to the net and jump.',
      'Get there early enough to be still before you leave the ground.',
    ],
    cue: 'Arrive early, then jump. Late blockers reach and lose.',
  },
  {
    id: 'block-read', name: 'Read the Setter', focus: 'blocking', equipment: 'net',
    positions: ['MB', 'OH', 'OPP'], work: '3 rounds of 10',
    how: [
      'Watch a setter, or a partner pretending to set, and call the direction out loud.',
      'Move on your call and commit fully.',
      'Score how many calls were right.',
    ],
    cue: 'Watch the setter\'s hands, not the ball.',
  },
  {
    id: 'block-land-soft', name: 'Landing Drill', focus: 'blocking', equipment: 'none',
    positions: ['all'], work: '3 rounds of 10',
    how: [
      'Jump as if blocking and focus entirely on the landing.',
      'Land on the balls of both feet, absorb through bent knees and hips.',
      'Make it silent. Noise means the joints took it instead of the muscles.',
    ],
    cue: 'Land quiet. Your knees will thank you in two years.',
  },

  // -------------------------------------------------------------- defense
  {
    id: 'defensive-stance', name: 'Defensive Stance Hold', focus: 'defense', equipment: 'none',
    positions: ['all'], work: '3 rounds of 30 seconds',
    how: [
      'Feet wide, weight on the balls of your feet, hips low, hands out in front.',
      'Shoulders in front of your knees, knees in front of your toes.',
      'Hold it and feel where it burns.',
    ],
    cue: 'If you can stand up quickly, you are not low enough.',
  },
  {
    id: 'wall-dig', name: 'Wall Digs', focus: 'defense', equipment: 'wall',
    positions: ['L', 'DS', 'OH'], work: '4 rounds of 20',
    how: [
      'Throw the ball hard into the wall from close range.',
      'Dig the fast rebound up and high in front of you.',
      'Stay low the whole round.',
    ],
    cue: 'Beat the ball to the spot, then be still.',
  },
  {
    id: 'sprawl', name: 'Sprawl', focus: 'defense', equipment: 'none',
    positions: ['L', 'DS'], work: '3 rounds of 8',
    how: [
      'From a low stance, step out and extend forward onto your chest and forearms.',
      'Slide, do not land on your knees or elbows.',
      'Get up quickly and reset.',
    ],
    cue: 'Step first, then go down. Never dive from standing.',
  },
  {
    id: 'roll-recover', name: 'Roll and Recover', focus: 'defense', equipment: 'none',
    positions: ['L', 'DS'], work: '3 rounds of 6 each side',
    setup: 'Do this on a soft surface, mat or grass.',
    how: [
      'From a low lunge to the side, play an imaginary ball then roll over your shoulder.',
      'Come back up to your feet in one motion.',
      'Keep your chin tucked and never roll over your head or neck.',
    ],
    cue: 'Over the shoulder, never over the head.',
  },
  {
    id: 'reaction-dig', name: 'Blind Reaction Dig', focus: 'defense', equipment: 'wall',
    positions: ['L', 'DS'], work: '3 rounds of 12',
    how: [
      'Face away from the wall, throw the ball over your shoulder into it.',
      'Turn as it leaves your hand and dig the rebound.',
      'Accept that you will miss some. That is the drill.',
    ],
    cue: 'Late eyes, quick feet.',
  },
  {
    id: 'pursuit', name: 'Pursuit Run', focus: 'defense', equipment: 'none',
    positions: ['all'], work: '4 rounds of 6',
    setup: 'Mark a spot six metres away.',
    how: [
      'From a defensive stance, sprint to the mark, play an imaginary ball high.',
      'Sprint back to your start and reset low.',
      'No jogging, ever.',
    ],
    cue: 'Chase everything. The ball is never dead until it lands.',
  },
  {
    id: 'overhead-dig', name: 'Overhead Dig', focus: 'defense', equipment: 'wall',
    positions: ['L', 'DS', 'S'], work: '3 rounds of 15',
    how: [
      'Throw the ball high off the wall so it comes back above your head.',
      'Play it with firm hands overhead rather than dropping to a platform.',
      'Push it high and forward.',
    ],
    cue: 'Firm hands, no swinging elbows.',
  },

  // -------------------------------------------------------------- jumping
  {
    id: 'approach-jump-max', name: 'Max Approach Jump', focus: 'jumping', equipment: 'none',
    positions: ['all'], work: '5 jumps, full rest between each',
    how: [
      'Run your full approach and jump as high as you possibly can.',
      'Reach with one hand and mark the height if you can.',
      'Rest a full minute so each one is fresh.',
    ],
    cue: 'Five great jumps beats fifty tired ones.',
  },
  {
    id: 'block-jump-repeat', name: 'Repeat Block Jumps', focus: 'jumping', equipment: 'none',
    positions: ['MB', 'OH', 'OPP'], work: '4 rounds of 5',
    how: [
      'Jump, land, and jump again immediately with minimal ground time.',
      'Keep your arms up throughout.',
      'Stop the round the moment your jumps get noticeably lower.',
    ],
    cue: 'Off the floor fast. Quality ends the set, not a number.',
  },
  {
    id: 'depth-drop', name: 'Drop Landing', focus: 'jumping', equipment: 'none',
    positions: ['all'], work: '3 rounds of 6',
    setup: 'A step or low box, about knee height. Nothing higher.',
    how: [
      'Step off the box, do not jump off.',
      'Land on both feet and absorb into a quarter squat.',
      'Hold the landing still for two seconds.',
    ],
    cue: 'Stick it. If you wobble, the box is too high.',
  },
  {
    id: 'calf-raise', name: 'Slow Calf Raises', focus: 'jumping', equipment: 'none',
    positions: ['all'], work: '3 sets of 15 each leg',
    how: [
      'Stand on one leg with the ball of your foot on a step.',
      'Rise up slowly, then lower even more slowly below the step.',
      'Use a wall for balance only.',
    ],
    cue: 'Three seconds down. The lowering is the point.',
  },
  {
    id: 'split-squat-vb', name: 'Rear Foot Elevated Split Squat', focus: 'jumping', equipment: 'none',
    positions: ['all'], work: '3 sets of 8 each leg',
    setup: 'A bench or step for the back foot.',
    how: [
      'Rest the top of your back foot behind you on the step.',
      'Lower until the front thigh is level with the ground.',
      'Drive up through the front heel.',
    ],
    cue: 'Front shin upright, hips square.',
  },
  {
    id: 'lateral-bound', name: 'Lateral Bounds', focus: 'jumping', equipment: 'none',
    positions: ['L', 'DS', 'OH'], work: '4 sets of 8',
    how: [
      'Push off one leg sideways and land balanced on the other.',
      'Hold the landing for a beat before going back.',
      'Cover as much ground as you can control.',
    ],
    cue: 'Stick every landing before the next push.',
  },
  {
    id: 'trap-bar-vb', name: 'Trap Bar Deadlift', focus: 'jumping', equipment: 'gym',
    positions: ['all'], work: '4 sets of 5',
    how: [
      'Stand inside the bar, feet hip width, chest tall and back flat.',
      'Push the floor away and stand up. Lower under control.',
      'Use a weight you could manage for eight.',
    ],
    cue: 'Form over weight, always. Have a coach watch this one.',
  },

  // --------------------------------------------------------- conditioning
  {
    id: 'court-sprints', name: 'Court Sprints', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '6 rounds with 45 seconds rest',
    setup: 'Mark out roughly the length of a court.',
    how: [
      'Sprint the length, touch the line, sprint back.',
      'Touch every line with your hand.',
      'Rest and repeat.',
    ],
    cue: 'The turns are the work. Stay low through them.',
  },
  {
    id: 'rally-intervals', name: 'Rally Intervals', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '10 rounds',
    how: [
      'Work hard for fifteen seconds: shuffles, sprawls, jumps, in any order.',
      'Rest for twenty seconds, like the gap between rallies.',
      'Repeat ten times without stopping early.',
    ],
    cue: 'Volleyball is short bursts with short rest. Train that shape.',
  },
  {
    id: 'shuffle-conditioning-vb', name: 'Shuffle Squares', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '4 laps each direction',
    setup: 'Four markers in a square, four metres a side.',
    how: [
      'Shuffle one side, backpedal the next, shuffle, then sprint the last.',
      'Stay low the whole lap.',
      'Rest thirty seconds between laps.',
    ],
    cue: 'Never cross your feet on the shuffles.',
  },
  {
    id: 'core-plank', name: 'Plank Series', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '3 rounds',
    how: [
      'Hold a front plank for 30 seconds, then each side for 20 seconds.',
      'Keep a straight line from heel to head, hips level.',
      'Breathe normally the whole time.',
    ],
    cue: 'Squeeze the glutes. A sagging plank does nothing.',
  },
  {
    id: 'shoulder-warmup', name: 'Shoulder Warm Up', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, before every session',
    how: [
      'Arm circles forward and back, small building to large.',
      'Cross body swings, then overhead reaches.',
      'Finish with ten slow practice arm swings.',
    ],
    cue: 'Never take a full swing at anything cold.',
  },
  {
    id: 'cooldown-vb', name: 'Cool Down and Breathe', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, every session',
    how: [
      'Walk easily for three minutes until your breathing settles.',
      'Then breathe in for four seconds and out for six, for two minutes.',
      'Drink water while you do it.',
    ],
    cue: 'The session is not over until your heart rate is down.',
  },
];
