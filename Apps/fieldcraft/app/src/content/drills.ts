// Fieldcraft drill library.
//
// Every drill is written to be run alone, safely, on open ground. Contact work
// is form only: there is never another player to hit. See the disclaimer.
//
// equipment is the MINIMUM needed. The ladder is:
//   none  -> open space, nothing else
//   ball  -> a football and space
//   cones -> cones (or shoes, bags, water bottles) and a field
//   gym   -> field plus a weight room

export type Focus =
  | 'speed' | 'agility' | 'power' | 'hands'
  | 'routes' | 'throwing' | 'blocking' | 'conditioning';

export type Equipment = 'none' | 'ball' | 'cones' | 'gym';

export type Drill = {
  id: string;
  name: string;
  focus: Focus;
  equipment: Equipment;
  /** Positions this suits best. 'all' means everyone. */
  positions: string[];
  /** What one round of work looks like. */
  work: string;
  /** How to set the ground up, if anything is needed. */
  setup?: string;
  /** The steps, in order. */
  how: string[];
  /** The one thing to think about while doing it. */
  cue: string;
};

export const DRILLS: Drill[] = [
  // ---------------------------------------------------------------- speed
  {
    id: 'wall-drive',
    name: 'Wall Drive Hold',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '3 rounds of 20 seconds each leg',
    how: [
      'Lean into a wall with straight arms so your body makes one long line from heel to head.',
      'Drive one knee up until the thigh is level with the ground, toe pulled up towards your shin.',
      'Hold it still. Do not let your hips sag or your back arch.',
    ],
    cue: 'One straight line from the back heel to the top of the head.',
  },
  {
    id: 'wall-switch',
    name: 'Wall Switches',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '4 rounds of 6 switches each side',
    how: [
      'Take the same lean position against the wall.',
      'Snap the legs so the front and back swap places, landing on the ball of the foot.',
      'Freeze for a second in the new position before the next switch.',
    ],
    cue: 'Punch the knee up fast, put the foot down faster.',
  },
  {
    id: 'aframe-start',
    name: 'Falling Start',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '6 starts, walk back between each',
    how: [
      'Stand tall with your weight on the balls of your feet.',
      'Let your whole body tip forward without bending at the waist.',
      'When you cannot hold it any longer, run. Take the first five steps low and long.',
    ],
    cue: 'Fall first, then run. Do not step until gravity makes you.',
  },
  {
    id: 'ten-yard-build',
    name: 'Ten Yard Build Ups',
    focus: 'speed', equipment: 'cones', positions: ['all'],
    work: '6 runs with a full walk back',
    setup: 'Three cones in a line, ten yards apart.',
    how: [
      'Jog the first ten yards.',
      'Build to about three quarter speed over the second ten.',
      'Hold that speed through the last cone, then slow down gradually.',
    ],
    cue: 'Speed should arrive smoothly, not in a jerk.',
  },
  {
    id: 'flying-twenty',
    name: 'Flying Twenty',
    focus: 'speed', equipment: 'cones', positions: ['all'],
    work: '4 runs, 2 minutes rest between each',
    setup: 'Twenty yards to build up, then twenty yards marked to sprint.',
    how: [
      'Use the first twenty yards to get up to near top speed.',
      'Sprint the marked twenty as fast as you can hold good form.',
      'Slow down over the following twenty. Never stop dead.',
    ],
    cue: 'Relax your jaw and hands. Tension makes you slower, not faster.',
  },
  {
    id: 'arm-action',
    name: 'Seated Arm Action',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '3 rounds of 15 seconds',
    how: [
      'Sit tall on the ground with your legs straight out in front.',
      'Drive your arms as if sprinting, hand from cheek to hip pocket.',
      'Keep the elbow angle steady and let the shoulder do the work.',
    ],
    cue: 'Hand to the cheek, hand to the pocket, nothing across the body.',
  },
  {
    id: 'skip-for-height',
    name: 'A Skip',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '4 lengths of 20 yards',
    how: [
      'Skip forward, driving one knee up to hip height each time.',
      'The foot comes down under your hip, not out in front.',
      'Stay tall and land on the ball of the foot.',
    ],
    cue: 'Down and back, not out and in front.',
  },
  {
    id: 'hill-sprint',
    name: 'Short Hill Sprints',
    focus: 'speed', equipment: 'none', positions: ['all'],
    work: '6 sprints of 8 seconds, walk down to recover',
    setup: 'A grass slope that is steep enough to feel but not to stumble on.',
    how: [
      'Start from a standing lean at the bottom.',
      'Drive up the hill for about eight seconds, low and hard.',
      'Walk all the way down before the next one.',
    ],
    cue: 'The hill puts you in the right shape. Let it.',
  },

  // -------------------------------------------------------------- agility
  {
    id: 'five-ten-five',
    name: 'Five Ten Five',
    focus: 'agility', equipment: 'cones', positions: ['all'],
    work: '6 runs, alternating which way you start',
    setup: 'Three cones in a line, five yards between each.',
    how: [
      'Start straddling the middle cone in a low stance.',
      'Sprint five yards to one side and touch the line with your hand.',
      'Turn and sprint ten yards across to the far cone and touch.',
      'Turn again and finish through the middle.',
    ],
    cue: 'Drop your hips before the turn, not during it.',
  },
  {
    id: 'l-drill',
    name: 'L Drill',
    focus: 'agility', equipment: 'cones', positions: ['all'],
    work: '4 runs each direction',
    setup: 'Three cones making an L, five yards apart.',
    how: [
      'Sprint five yards to the second cone and touch the ground.',
      'Return to the start and touch again.',
      'Sprint back to the second cone, turn tight around it, and weave the L before finishing.',
    ],
    cue: 'Lean into the turn like a motorbike, do not run it square.',
  },
  {
    id: 'w-drill',
    name: 'W Pattern',
    focus: 'agility', equipment: 'cones', positions: ['DB', 'WR', 'LB'],
    work: '4 trips through',
    setup: 'Five cones in a zig zag, five yards apart.',
    how: [
      'Backpedal to the first cone.',
      'Break forward at an angle to the next.',
      'Alternate backpedal and forward break through the whole pattern.',
    ],
    cue: 'Keep your shoulders in front of your hips the whole way.',
  },
  {
    id: 'mirror-shuffle',
    name: 'Lateral Shuffle Squares',
    focus: 'agility', equipment: 'cones', positions: ['all'],
    work: '4 laps each direction',
    setup: 'Four cones in a square, five yards a side.',
    how: [
      'Shuffle along the first side without crossing your feet.',
      'Backpedal the second, shuffle the third, sprint the fourth.',
      'Stay low the whole lap.',
    ],
    cue: 'Never click your heels together. Push the ground away sideways.',
  },
  {
    id: 'hip-flip',
    name: 'Hip Flips',
    focus: 'agility', equipment: 'none', positions: ['DB', 'LB', 'TE'],
    work: '3 rounds of 8 flips',
    how: [
      'Start in a low stance facing forward.',
      'Open your hips and turn ninety degrees, landing balanced and low.',
      'Snap back the other way without standing up.',
    ],
    cue: 'Turn the belt buckle, and the feet follow.',
  },
  {
    id: 'line-hops',
    name: 'Line Hops',
    focus: 'agility', equipment: 'none', positions: ['all'],
    work: '4 rounds of 20 seconds',
    setup: 'Any straight line on the ground.',
    how: [
      'Hop side to side over the line on both feet, staying on the balls of your feet.',
      'Keep the contacts quick and quiet.',
      'Repeat facing forwards, then hopping front to back.',
    ],
    cue: 'Quiet feet. Noise means you are landing heavy.',
  },
  {
    id: 'three-cone-weave',
    name: 'Cone Weave',
    focus: 'agility', equipment: 'cones', positions: ['RB', 'WR', 'QB'],
    work: '6 trips',
    setup: 'Six cones in a line, two yards apart.',
    how: [
      'Run through the cones, planting outside foot to change direction each time.',
      'Keep your shoulders square down the field.',
      'Accelerate out of the last cone for five yards.',
    ],
    cue: 'Cut off the outside foot, not the inside one.',
  },
  {
    id: 'reaction-turn',
    name: 'Blind Turn and Go',
    focus: 'agility', equipment: 'none', positions: ['all'],
    work: '8 reps',
    how: [
      'Stand facing away from the field with your eyes closed.',
      'Count three seconds, open your eyes, turn and sprint ten yards.',
      'Alternate turning left and right.',
    ],
    cue: 'Find your balance before your speed.',
  },

  // ---------------------------------------------------------------- hands
  {
    id: 'wall-toss',
    name: 'Wall Tosses',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE', 'RB', 'DB'],
    work: '4 rounds of 20 catches',
    how: [
      'Stand about five yards from a solid wall.',
      'Throw the ball against the wall and catch the rebound with your hands only.',
      'Never let it touch your chest. Vary the height every few throws.',
    ],
    cue: 'Thumbs together high, pinkies together low.',
  },
  {
    id: 'one-hand-wall',
    name: 'One Hand Wall Catches',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE'],
    work: '3 rounds of 10 each hand',
    how: [
      'Stand three yards from the wall.',
      'Toss underhand and catch the rebound with one hand only.',
      'Squeeze the point of the ball, then tuck it away before the next rep.',
    ],
    cue: 'Catch the tip, not the fat of the ball.',
  },
  {
    id: 'eyes-tuck',
    name: 'Look It In and Tuck',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE', 'RB'],
    work: '3 rounds of 15',
    how: [
      'Toss the ball up above your head and track it all the way into your hands.',
      'Watch it into the tuck, not up the field.',
      'Secure it high and tight before you look anywhere else.',
    ],
    cue: 'Eyes stay on the ball one full second after you have it.',
  },
  {
    id: 'high-point',
    name: 'High Point Catches',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE'],
    work: '3 rounds of 10',
    how: [
      'Throw the ball high in front of you.',
      'Time your run so you catch it at the highest point you can reach.',
      'Land balanced on both feet with the ball secured.',
    ],
    cue: 'Attack the ball at its peak. Do not wait for it to come down.',
  },
  {
    id: 'over-shoulder',
    name: 'Over the Shoulder Catch',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE', 'DB'],
    work: '3 rounds of 8 each side',
    how: [
      'Toss the ball forward and over your own head, then run under it.',
      'Look back over the same shoulder the ball is falling on.',
      'Catch it in your hands without breaking stride.',
    ],
    cue: 'Turn the head, not the whole body. Keep running.',
  },
  {
    id: 'ball-security',
    name: 'Four Point Ball Security',
    focus: 'hands', equipment: 'ball', positions: ['RB', 'WR', 'TE', 'QB'],
    work: '3 rounds of 30 seconds each arm',
    how: [
      'Hold the ball with the point covered by your fingers, forearm along the side, ball against the ribs, elbow squeezed down.',
      'Jog twenty yards holding all four points.',
      'Have someone slap at it if anyone is around, otherwise slap at it yourself with the free hand.',
    ],
    cue: 'Fingers over the point, elbow locked to the ribs.',
  },
  {
    id: 'switch-hands',
    name: 'Running Hand Switch',
    focus: 'hands', equipment: 'ball', positions: ['RB', 'WR'],
    work: '4 lengths of 20 yards',
    how: [
      'Jog holding the ball in four point security.',
      'Every five yards, switch the ball to the other arm across your body in one motion.',
      'Reset all four points immediately after each switch.',
    ],
    cue: 'Switch high across the chest, never low near the waist.',
  },
  {
    id: 'bad-ball',
    name: 'Bad Ball Drill',
    focus: 'hands', equipment: 'ball', positions: ['WR', 'TE', 'RB'],
    work: '3 rounds of 12',
    how: [
      'Throw the ball off a wall at deliberately awkward angles, low, wide and behind you.',
      'Adjust and catch whatever comes back.',
      'Reset and repeat without letting the ball hit the ground.',
    ],
    cue: 'Move your feet to the ball instead of reaching for it.',
  },

  // --------------------------------------------------------------- routes
  {
    id: 'release-footwork',
    name: 'Line of Scrimmage Release',
    focus: 'routes', equipment: 'cones', positions: ['WR', 'TE'],
    work: '4 rounds of 6 each direction',
    setup: 'One cone as the defender.',
    how: [
      'Start in your stance directly in front of the cone.',
      'Take a hard jab step one way, then cross over and accelerate past the other side.',
      'Clear the cone within two steps.',
    ],
    cue: 'Sell the first step, win with the second.',
  },
  {
    id: 'stem-and-break',
    name: 'Stem and Break',
    focus: 'routes', equipment: 'cones', positions: ['WR', 'TE'],
    work: '6 reps each side',
    setup: 'A cone ten yards downfield.',
    how: [
      'Sprint at the cone as if it is a defender.',
      'Over the last three steps, drop your hips and shorten your stride.',
      'Break hard at ninety degrees and accelerate five yards.',
    ],
    cue: 'Get low before the break, or the break is slow.',
  },
  {
    id: 'speed-cut',
    name: 'Speed Cut',
    focus: 'routes', equipment: 'cones', positions: ['WR', 'TE', 'RB'],
    work: '6 reps each side',
    setup: 'A cone twelve yards downfield.',
    how: [
      'Run at full speed to the cone.',
      'Round the cut slightly without slowing, leaning into the turn.',
      'Come out of it at the same speed you went in.',
    ],
    cue: 'A speed cut keeps the speed. If you slowed, it was a stop.',
  },
  {
    id: 'comeback',
    name: 'Comeback Route',
    focus: 'routes', equipment: 'cones', positions: ['WR', 'TE'],
    work: '5 reps each side',
    setup: 'A cone fifteen yards downfield.',
    how: [
      'Sprint to the cone selling a deep route.',
      'Sink your hips, plant, and come back downhill towards the sideline for three yards.',
      'Finish with your hands ready and eyes back to the quarterback.',
    ],
    cue: 'Sell deep hard enough that the comeback is free.',
  },
  {
    id: 'route-tree',
    name: 'Route Tree Walkthrough',
    focus: 'routes', equipment: 'cones', positions: ['WR', 'TE'],
    work: 'One full tree at walking pace, then one at half speed',
    setup: 'Cones marking five, ten and fifteen yards.',
    how: [
      'Walk each route in order, saying the name out loud as you run it.',
      'Focus on the depth being exactly right every time.',
      'Repeat the whole tree at half speed with the same depths.',
    ],
    cue: 'Depth first. A route at the wrong depth is a wrong route.',
  },
  {
    id: 'three-step-break',
    name: 'Three Step Break',
    focus: 'routes', equipment: 'none', positions: ['WR', 'TE'],
    work: '4 rounds of 8',
    how: [
      'Sprint five yards.',
      'Gather with three short chopping steps.',
      'Break flat across at full speed.',
    ],
    cue: 'Three steps, not four. Count them out loud.',
  },

  // ------------------------------------------------------------- throwing
  {
    id: 'grip-check',
    name: 'Grip and Wrist Snap',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '3 rounds of 20 snaps',
    how: [
      'Hold the ball with your fingers on the laces and a gap between palm and ball.',
      'Standing still, flick the ball a few feet in the air using only wrist and fingers.',
      'Watch that it spins tight and straight.',
    ],
    cue: 'The last thing to touch the ball is the index finger.',
  },
  {
    id: 'knee-throws',
    name: 'Kneeling Throws',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '20 throws at ten yards',
    setup: 'A wall or a partner ten yards away.',
    how: [
      'Kneel on your throwing side knee, other foot forward.',
      'Throw using only your upper body, no leg drive at all.',
      'Finish with the thumb pointing down past the opposite pocket.',
    ],
    cue: 'No legs means the arm has nowhere to hide.',
  },
  {
    id: 'hitch-throw',
    name: 'Three Step Drop and Throw',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '4 rounds of 8',
    how: [
      'Take a clean three step drop, pushing off hard on the first step.',
      'Hitch once to gather your feet under you.',
      'Throw to a target, stepping directly at it.',
    ],
    cue: 'The front foot points where the ball is going.',
  },
  {
    id: 'throw-on-move',
    name: 'Rollout Throws',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '6 each direction',
    how: [
      'Roll out to one side at controlled speed.',
      'Get your shoulders and hips turned back to the target before releasing.',
      'Throw without stopping dead.',
    ],
    cue: 'Turn the whole body. Never throw with the arm alone.',
  },
  {
    id: 'touch-throws',
    name: 'Touch and Trajectory',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '15 throws at each of three distances',
    setup: 'Targets at ten, twenty and thirty yards.',
    how: [
      'Throw a flat, hard ball at ten yards.',
      'Throw with a gentle arc at twenty.',
      'Throw a high deep ball at thirty that drops into the target.',
    ],
    cue: 'Same motion every time. Only the release angle changes.',
  },
  {
    id: 'footwork-ladder-qb',
    name: 'Quick Feet Into Throw',
    focus: 'throwing', equipment: 'ball', positions: ['QB'],
    work: '3 rounds of 6',
    how: [
      'Chop your feet fast in place for three seconds.',
      'On your own call, gather and throw immediately to a target.',
      'Reset and repeat.',
    ],
    cue: 'Busy feet, calm hands.',
  },

  // ---------------------------------------------------------------- power
  {
    id: 'broad-jump',
    name: 'Standing Broad Jump',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '5 jumps with full rest between each',
    how: [
      'Stand with feet under your hips on soft ground.',
      'Swing the arms back, dip the hips, and jump forward as far as you can.',
      'Land on both feet with bent knees and hold the landing still.',
    ],
    cue: 'Stick the landing. If you fall forward, it does not count.',
  },
  {
    id: 'vertical-jump',
    name: 'Countermovement Jump',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '4 rounds of 5',
    how: [
      'Stand tall, then dip quickly to about a quarter squat.',
      'Reverse straight out of the dip and jump as high as you can.',
      'Land softly and reset fully before the next one.',
    ],
    cue: 'The dip and the jump are one movement, not two.',
  },
  {
    id: 'bound',
    name: 'Alternating Bounds',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '4 sets of 8 bounds',
    how: [
      'From a jog, push off one leg and cover as much ground as you can before landing on the other.',
      'Swing the opposite arm hard with each bound.',
      'Land balanced and go straight into the next.',
    ],
    cue: 'Distance, not speed. Hang in the air.',
  },
  {
    id: 'split-squat',
    name: 'Rear Foot Elevated Split Squat',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '3 sets of 8 each leg',
    setup: 'A bench, step or low wall to rest the back foot on.',
    how: [
      'Rest the top of the back foot behind you on the step.',
      'Lower until the front thigh is about level with the ground.',
      'Drive up through the front heel.',
    ],
    cue: 'Front shin stays close to upright.',
  },
  {
    id: 'hip-bridge',
    name: 'Single Leg Hip Bridge',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '3 sets of 10 each side',
    how: [
      'Lie on your back with one foot planted and the other leg straight out.',
      'Drive the hips up through the planted heel until the body makes a straight line.',
      'Lower slowly under control.',
    ],
    cue: 'Squeeze the glute at the top, do not arch the lower back.',
  },
  {
    id: 'nordic-hamstring',
    name: 'Assisted Hamstring Lower',
    focus: 'power', equipment: 'none', positions: ['all'],
    work: '3 sets of 5',
    setup: 'Something solid to hook your heels under, and a cushion for the knees.',
    how: [
      'Kneel with your heels held down and your body straight from knee to head.',
      'Lower forward as slowly as you can, resisting the whole way.',
      'Catch yourself with your hands and push back to the start.',
    ],
    cue: 'Fight the fall. Slow is the entire point.',
  },
  {
    id: 'med-ball-throw',
    name: 'Overhead Throw for Distance',
    focus: 'power', equipment: 'gym', positions: ['all'],
    work: '5 throws with full rest',
    how: [
      'Hold a medicine ball overhead with both hands.',
      'Dip the hips and throw the ball forward as far as possible.',
      'Follow through and let the whole body go with it.',
    ],
    cue: 'Power starts at the hips, not the shoulders.',
  },
  {
    id: 'trap-bar-pull',
    name: 'Trap Bar Deadlift',
    focus: 'power', equipment: 'gym', positions: ['all'],
    work: '4 sets of 5 at a weight you could do 8 with',
    how: [
      'Stand inside the bar with feet hip width.',
      'Grip the handles, set your chest tall and your back flat.',
      'Push the floor away and stand up. Lower under control.',
    ],
    cue: 'Never chase weight over form. Have a coach watch this one.',
  },

  // ------------------------------------------------- blocking / tackling form
  {
    id: 'stance-start',
    name: 'Stance and Start',
    focus: 'blocking', equipment: 'none', positions: ['OL', 'DL', 'TE'],
    work: '4 rounds of 8',
    how: [
      'Set your stance with feet just wider than your hips and weight on the balls of your feet.',
      'On your own count, fire out low and take three hard steps.',
      'Reset and repeat.',
    ],
    cue: 'The first step is short and hard, not long and slow.',
  },
  {
    id: 'hand-placement',
    name: 'Hand Placement on Air',
    focus: 'blocking', equipment: 'none', positions: ['OL', 'TE'],
    work: '3 rounds of 10',
    how: [
      'From your stance, step and punch both hands forward to where a chest plate would be.',
      'Thumbs up, elbows tight to your body.',
      'Freeze and check your hands are inside, not out wide.',
    ],
    cue: 'Inside hands win. Outside hands get flagged.',
  },
  {
    id: 'mirror-slide',
    name: 'Pass Set Slide',
    focus: 'blocking', equipment: 'cones', positions: ['OL'],
    work: '4 rounds of 20 seconds',
    setup: 'Two cones five yards apart.',
    how: [
      'Set in pass protection posture between the cones.',
      'Slide side to side without crossing your feet or standing up.',
      'Keep your hands up and ready the whole time.',
    ],
    cue: 'Kick with the near foot, then slide the far one.',
  },
  {
    id: 'fit-position',
    name: 'Tackle Fit Position',
    focus: 'blocking', equipment: 'none', positions: ['DL', 'LB', 'DB'],
    work: '3 rounds of 8 holds',
    how: [
      'Step into a low position with knees bent, back flat, and eyes up.',
      'Bring both arms up as if wrapping, chest tall, head to one side of an imaginary ball carrier.',
      'Hold for three seconds and check your head is up and never down.',
    ],
    cue: 'Eyes up, head across, never lead with the crown.',
  },
  {
    id: 'angle-approach',
    name: 'Angle Approach',
    focus: 'blocking', equipment: 'cones', positions: ['DL', 'LB', 'DB'],
    work: '6 reps each side',
    setup: 'One cone as the ball carrier.',
    how: [
      'Start ten yards from the cone at an angle.',
      'Close the distance fast, then break down into short choppy steps over the last three yards.',
      'Finish in fit position beside the cone. Never hit it.',
    ],
    cue: 'Sprint to the fight, then gather. Do not arrive out of control.',
  },
  {
    id: 'shed-hands',
    name: 'Hand Shed on Air',
    focus: 'blocking', equipment: 'none', positions: ['DL', 'LB'],
    work: '3 rounds of 10 each side',
    how: [
      'From your stance, punch both hands out as if hitting a blocker.',
      'Rip one arm up and through while turning your hips past the imaginary block.',
      'Accelerate two steps out of the shed.',
    ],
    cue: 'Get off the block, not around it.',
  },
  {
    id: 'drive-steps',
    name: 'Drive Block Steps',
    focus: 'blocking', equipment: 'none', positions: ['OL', 'TE'],
    work: '4 rounds of 6',
    how: [
      'From your stance, take six short driving steps forward staying low the whole way.',
      'Keep your feet moving and never let them stop under you.',
      'Finish with your hips lower than your shoulders.',
    ],
    cue: 'Short steps, wide base, feet never stop.',
  },

  // --------------------------------------------------------- conditioning
  {
    id: 'gassers',
    name: 'Gassers',
    focus: 'conditioning', equipment: 'cones', positions: ['all'],
    work: '4 gassers with 90 seconds rest between',
    setup: 'The width of a field, or fifty yards marked out.',
    how: [
      'Sprint across and back, then across and back again without stopping.',
      'Rest fully, then repeat.',
      'Stop the session if your times fall off badly.',
    ],
    cue: 'Even effort across all four. Do not win the first and die on the last.',
  },
  {
    id: 'tempo-runs',
    name: 'Tempo Hundreds',
    focus: 'conditioning', equipment: 'cones', positions: ['all'],
    work: '8 runs of 100 yards at about 70 percent, walking back between',
    how: [
      'Run the hundred at a relaxed, controlled speed that feels smooth.',
      'Walk back slowly as your rest.',
      'Keep every run within a second or two of the others.',
    ],
    cue: 'This is not a sprint session. Smooth beats fast here.',
  },
  {
    id: 'perfect-plays',
    name: 'Perfect Play Intervals',
    focus: 'conditioning', equipment: 'none', positions: ['all'],
    work: '12 reps with 25 seconds rest',
    how: [
      'Sprint hard for six seconds, roughly the length of a real play.',
      'Rest exactly twenty five seconds, like a play clock.',
      'Repeat for twelve plays, which is about one drive.',
    ],
    cue: 'Football is short bursts with short rest. Train the real shape.',
  },
  {
    id: 'up-downs',
    name: 'Up Downs',
    focus: 'conditioning', equipment: 'none', positions: ['all'],
    work: '4 rounds of 30 seconds',
    how: [
      'Chop your feet fast in place.',
      'On your own call, drop to your chest and get straight back up chopping.',
      'Keep the feet moving the whole round.',
    ],
    cue: 'Get up faster than you went down.',
  },
  {
    id: 'sled-push',
    name: 'Sled Push',
    focus: 'conditioning', equipment: 'gym', positions: ['all'],
    work: '6 pushes of 20 yards',
    how: [
      'Load the sled so twenty yards is hard but never forces you upright.',
      'Push with a flat back, arms locked, driving through short steps.',
      'Walk back as recovery.',
    ],
    cue: 'If you stand up, the weight is too heavy.',
  },
  {
    id: 'shuttle-conditioning',
    name: 'Three Cone Shuttle Repeats',
    focus: 'conditioning', equipment: 'cones', positions: ['all'],
    work: '6 rounds with 45 seconds rest',
    setup: 'Cones at zero, ten and twenty yards.',
    how: [
      'Sprint to the ten and back, then to the twenty and back.',
      'Touch the line with your hand at each turn.',
      'Rest and repeat.',
    ],
    cue: 'The turns are where the work is. Stay low through them.',
  },
  {
    id: 'cooldown-walk',
    name: 'Cool Down and Breathe',
    focus: 'conditioning', equipment: 'none', positions: ['all'],
    work: '5 minutes, every session',
    how: [
      'Walk easily for three minutes until your breathing settles.',
      'Then breathe in for four seconds and out for six, for two minutes.',
      'Drink water while you do it.',
    ],
    cue: 'The session is not over until your heart rate is back down.',
  },
];
