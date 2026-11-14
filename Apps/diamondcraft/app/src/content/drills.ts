// Diamondcraft drill library. Written to be run alone, safely.
//
// equipment is the MINIMUM needed:
//   none  -> open space        ball  -> a ball and a glove
//   tee   -> tee, bat and net  field -> a field
//   gym   -> field plus a weight room

export type Focus =
  | 'hitting' | 'throwing' | 'fielding' | 'pitching'
  | 'catching' | 'speed' | 'power' | 'conditioning';

export type Equipment = 'none' | 'ball' | 'tee' | 'field' | 'gym';

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
  // -------------------------------------------------------------- hitting
  {
    id: 'stance-load', name: 'Stance and Load', focus: 'hitting', equipment: 'none',
    positions: ['all'], work: '3 rounds of 15',
    how: [
      'Set your stance, weight balanced over the middle of both feet.',
      'Shift your weight back into your back hip without drifting backwards.',
      'Hold the loaded position for a second, then reset.',
    ],
    cue: 'Load into the hip, not onto the heel.',
  },
  {
    id: 'tee-work', name: 'Tee Work', focus: 'hitting', equipment: 'tee',
    positions: ['all'], work: '4 rounds of 15 swings',
    setup: 'Tee set at the middle of your strike zone, net checked for holes.',
    how: [
      'Take full swings, watching the ball all the way off the tee.',
      'Finish balanced, do not fall away.',
      'Reset your stance between every swing.',
    ],
    cue: 'Quality over quantity. Fifteen good swings beats fifty tired ones.',
  },
  {
    id: 'tee-zones', name: 'Tee Zones', focus: 'hitting', equipment: 'tee',
    positions: ['all'], work: '10 swings at each of 3 heights',
    how: [
      'Set the tee low, then middle, then high.',
      'Adjust with your legs, keeping the same swing shape.',
      'Note which height you are worst at and give it an extra round.',
    ],
    cue: 'The swing does not change. The body height does.',
  },
  {
    id: 'inside-outside', name: 'Inside and Outside', focus: 'hitting', equipment: 'tee',
    positions: ['all'], work: '10 swings at each position',
    how: [
      'Move the tee in front of your front hip, then back to the middle, then deeper.',
      'Drive the in front ball to the pull side and the deep one the other way.',
      'Let contact point decide direction, not your hands.',
    ],
    cue: 'Hit it where it is pitched.',
  },
  {
    id: 'one-hand-swing', name: 'One Hand Swings', focus: 'hitting', equipment: 'tee',
    positions: ['all'], work: '3 rounds of 8 each hand',
    setup: 'Use a lighter bat, choked up.',
    how: [
      'Swing with the top hand only, then the bottom hand only.',
      'Keep the path short and direct to the ball.',
      'Stay slow and controlled. This is a feel drill, not a power drill.',
    ],
    cue: 'Feel which hand is doing what in your real swing.',
  },
  {
    id: 'mirror-swing', name: 'Mirror Swings', focus: 'hitting', equipment: 'none',
    positions: ['all'], work: '3 rounds of 10',
    how: [
      'Swing slowly in front of a mirror or a window reflection.',
      'Stop at contact and check your hands, hips and head position.',
      'Fix one thing at a time.',
    ],
    cue: 'You cannot fix what you have never seen.',
  },
  {
    id: 'two-strike', name: 'Two Strike Approach', focus: 'hitting', equipment: 'tee',
    positions: ['all'], work: '3 rounds of 12',
    how: [
      'Choke up, widen your stance slightly and shorten your stride.',
      'Take controlled swings aimed at driving the ball back up the middle.',
      'Think contact, not damage.',
    ],
    cue: 'Two strikes is a different job. Practise it as one.',
  },

  // ------------------------------------------------------------- throwing
  {
    id: 'wrist-flips', name: 'Wrist Flips', focus: 'throwing', equipment: 'ball',
    positions: ['all'], work: '2 rounds of 20',
    setup: 'A wall or partner, five metres away.',
    how: [
      'Hold the ball across the seams, elbow up and forearm vertical.',
      'Flip the ball with the wrist and fingers only.',
      'Watch for tight backspin.',
    ],
    cue: 'Fingers behind the ball. Backspin means good release.',
  },
  {
    id: 'four-seam-grip', name: 'Four Seam Grip Check', focus: 'throwing', equipment: 'ball',
    positions: ['all'], work: '3 rounds of 20 grabs',
    how: [
      'Hold the ball in your glove, look away, and find the four seam grip by feel.',
      'Check it, drop it back, and repeat.',
      'Build up until you find it every time without looking.',
    ],
    cue: 'You will never have time to look for the seams in a game.',
  },
  {
    id: 'long-toss', name: 'Long Toss Build Up', focus: 'throwing', equipment: 'field',
    positions: ['all'], work: '10 minutes, stepping back gradually',
    how: [
      'Start close and throw easy, stepping back a few metres every ten throws.',
      'Keep good form as the distance grows, never short arm it.',
      'Come back in close and finish with easy throws.',
    ],
    cue: 'Build out and come back in. Never finish at max distance.',
  },
  {
    id: 'throwing-footwork', name: 'Throwing Footwork', focus: 'throwing', equipment: 'ball',
    positions: ['IF', 'OF'], work: '3 rounds of 12',
    how: [
      'From a fielding position, shuffle your feet to line your front shoulder at the target.',
      'Step directly at the target with your front foot.',
      'Throw, then follow through towards the target.',
    ],
    cue: 'Feet aim the throw. The arm just delivers it.',
  },
  {
    id: 'crow-hop', name: 'Crow Hop', focus: 'throwing', equipment: 'ball',
    positions: ['OF'], work: '3 rounds of 10',
    how: [
      'Field the ball moving forward, hop onto your back foot, then stride and throw.',
      'Keep it low and long, one bounce to the target.',
      'Never throw flat footed from the outfield.',
    ],
    cue: 'Gather, hop, throw. Momentum makes the distance.',
  },
  {
    id: 'arm-care', name: 'Band Arm Care', focus: 'throwing', equipment: 'gym',
    positions: ['all'], work: '3 sets of 15 each way',
    how: [
      'With a light band, rotate the forearm outward with the elbow tucked.',
      'Then raise the arm to shoulder height and lower slowly.',
      'Keep it light and slow. This protects the arm, it does not build it.',
    ],
    cue: 'Do this every session. It is the cheapest insurance there is.',
  },
  {
    id: 'accuracy-target', name: 'Target Throwing', focus: 'throwing', equipment: 'ball',
    positions: ['all'], work: '4 rounds of 10',
    setup: 'Mark a chest height square on a wall or net.',
    how: [
      'Throw at the target from fifteen metres.',
      'Score a point for every hit and write the total down.',
      'Beat it next session.',
    ],
    cue: 'Chest height, every time. High throws cost bases.',
  },

  // ------------------------------------------------------------- fielding
  {
    id: 'ready-position', name: 'Ready Position Hold', focus: 'fielding', equipment: 'none',
    positions: ['IF', 'OF'], work: '3 rounds of 30 seconds',
    how: [
      'Feet wider than your shoulders, knees bent, hands out in front.',
      'Weight on the balls of your feet, chest over your knees.',
      'Hold it and feel where it burns.',
    ],
    cue: 'Low and wide. You cannot field from standing up.',
  },
  {
    id: 'glove-work', name: 'Short Hop Glove Work', focus: 'fielding', equipment: 'ball',
    positions: ['IF'], work: '4 rounds of 20',
    setup: 'A wall, from about three metres.',
    how: [
      'Throw the ball into the ground so it short hops back at you.',
      'Field it out in front with a soft glove, funnelling it to your middle.',
      'Stay down through the whole catch.',
    ],
    cue: 'Glove out front, palm up, give with it.',
  },
  {
    id: 'barehand', name: 'Barehand Rolls', focus: 'fielding', equipment: 'ball',
    positions: ['IF'], work: '3 rounds of 15',
    how: [
      'Roll the ball out, charge it, and pick it barehanded on the run.',
      'Field it beside your front foot, not underneath you.',
      'Come up throwing.',
    ],
    cue: 'Charge slow balls. Waiting turns outs into hits.',
  },
  {
    id: 'backhand-field', name: 'Backhand Pick', focus: 'fielding', equipment: 'ball',
    positions: ['IF'], work: '3 rounds of 12',
    how: [
      'Roll the ball to your glove side and reach across to field it backhanded.',
      'Get your glove side foot down as you field.',
      'Plant and throw.',
    ],
    cue: 'Backhand is a skill, not a mistake. Drill it.',
  },
  {
    id: 'fly-ball-tracking', name: 'Fly Ball Tracking', focus: 'fielding', equipment: 'ball',
    positions: ['OF'], work: '3 rounds of 12',
    how: [
      'Throw the ball high and to one side, then run under it.',
      'Get to the spot early and wait, rather than drifting under it.',
      'Catch it above your head with two hands.',
    ],
    cue: 'Beat the ball to the spot. Then be still.',
  },
  {
    id: 'first-step', name: 'First Step Reads', focus: 'fielding', equipment: 'none',
    positions: ['IF', 'OF'], work: '4 rounds of 8',
    how: [
      'From ready position, take one hard crossover step on a call you make yourself.',
      'Alternate left, right, forward and back.',
      'The first step should be a crossover, never a backwards hop.',
    ],
    cue: 'The first step decides the play.',
  },
  {
    id: 'double-play-turn', name: 'Double Play Footwork', focus: 'fielding', equipment: 'none',
    positions: ['IF'], work: '3 rounds of 10',
    setup: 'Mark a spot as the bag.',
    how: [
      'Approach the bag under control, touch it with the correct foot.',
      'Clear away from the runner line as you turn and throw.',
      'Practise both directions.',
    ],
    cue: 'Get off the bag before you throw. Safety first, speed second.',
  },

  // ------------------------------------------------------------- pitching
  {
    id: 'balance-point', name: 'Balance Point Hold', focus: 'pitching', equipment: 'none',
    positions: ['P'], work: '3 rounds of 10',
    how: [
      'Lift your front leg to the top of your delivery and stop.',
      'Hold for three seconds without wobbling.',
      'Lower under control and reset.',
    ],
    cue: 'If you cannot hold it, you cannot repeat it.',
  },
  {
    id: 'stride-line', name: 'Stride Line Check', focus: 'pitching', equipment: 'none',
    positions: ['P'], work: '3 rounds of 12',
    setup: 'A straight line on the ground pointing at your target.',
    how: [
      'Deliver without a ball and see where your front foot lands.',
      'It should land on or just inside the line, pointing at the target.',
      'Repeat until it lands the same place every time.',
    ],
    cue: 'Same landing spot every pitch. That is control.',
  },
  {
    id: 'towel-drill', name: 'Towel Drill', focus: 'pitching', equipment: 'none',
    positions: ['P'], work: '3 rounds of 12',
    setup: 'Hold a small towel in your throwing hand.',
    how: [
      'Go through your full delivery and snap the towel forward at release.',
      'Finish with your chest over your front knee.',
      'This lets you drill the motion without loading your arm.',
    ],
    cue: 'All the mechanics, none of the mileage.',
  },
  {
    id: 'flat-ground', name: 'Flat Ground Work', focus: 'pitching', equipment: 'ball',
    positions: ['P'], work: '20 pitches',
    how: [
      'Throw at a target from flat ground at controlled effort.',
      'Focus on repeating your release point, not on speed.',
      'Count strikes and write the number down.',
    ],
    cue: 'Command first. Velocity comes later and lasts longer.',
  },
  {
    id: 'bullpen-plan', name: 'Planned Bullpen', focus: 'pitching', equipment: 'field',
    positions: ['P'], work: '30 to 40 pitches',
    how: [
      'Write the sequence before you start, pitch type and location for each.',
      'Call each one out loud, then throw it.',
      'Score yourself on execution, not on how it felt.',
    ],
    cue: 'Never throw a bullpen without a plan.',
  },
  {
    id: 'hold-runners', name: 'Holding Runners', focus: 'pitching', equipment: 'none',
    positions: ['P'], work: '3 rounds of 10',
    how: [
      'Work from the stretch, varying how long you hold before delivering.',
      'Practise a quick delivery and a slide step.',
      'Keep your mechanics identical however long you hold.',
    ],
    cue: 'Vary the timing, never the motion.',
  },
  {
    id: 'pitch-count', name: 'Recovery Day', focus: 'pitching', equipment: 'none',
    positions: ['P'], work: 'Full rest, planned into the week',
    how: [
      'After a heavy throwing day, take a full day with no throwing at all.',
      'Do light band work, legs and conditioning instead.',
      'Track your throwing days so rest is planned, not accidental.',
    ],
    cue: 'Rest is part of the programme, not the absence of one.',
  },

  // ------------------------------------------------------------- catching
  {
    id: 'catcher-stance', name: 'Catching Stance Hold', focus: 'catching', equipment: 'none',
    positions: ['C'], work: '3 rounds of 30 seconds',
    how: [
      'Get into your receiving stance, weight on the balls of your feet.',
      'Keep your throwing hand behind your back or loosely behind the glove.',
      'Hold and breathe normally.',
    ],
    cue: 'Throwing hand tucked away. Fingers are worth protecting.',
  },
  {
    id: 'framing', name: 'Framing', focus: 'catching', equipment: 'ball',
    positions: ['C'], work: '4 rounds of 20',
    setup: 'A wall, from three metres.',
    how: [
      'Throw the ball off the wall and catch it at the edges of your zone.',
      'Receive it moving slightly towards the middle, and hold it still.',
      'Keep your body quiet. Only the glove moves.',
    ],
    cue: 'Catch the ball going in, then freeze.',
  },
  {
    id: 'blocking-catcher', name: 'Blocking Position', focus: 'catching', equipment: 'none',
    positions: ['C'], work: '4 rounds of 10',
    setup: 'Do this on a soft surface, with pads if you have them.',
    how: [
      'From your stance, drop to both knees with your chest angled down over the ball.',
      'Glove fills the gap between your legs, chin tucked to your chest.',
      'Get back up to your stance quickly.',
    ],
    cue: 'Chest over the ball, chin down, keep it in front.',
  },
  {
    id: 'pop-time', name: 'Pop Time Footwork', focus: 'catching', equipment: 'ball',
    positions: ['C'], work: '4 rounds of 8',
    how: [
      'From your stance, catch, replace your feet and get into throwing position.',
      'Time yourself from catch to release.',
      'Work on the feet, not on throwing harder.',
    ],
    cue: 'Quick feet make quick throws. The arm is the last part.',
  },
  {
    id: 'pop-up', name: 'Pop Up Turns', focus: 'catching', equipment: 'ball',
    positions: ['C'], work: '3 rounds of 10',
    how: [
      'Throw a ball straight up, turn your back to the field and find it.',
      'Let it drift towards you rather than reaching out.',
      'Catch it above your head with two hands.',
    ],
    cue: 'Turn your back to the infield. The ball always drifts that way.',
  },
  {
    id: 'receiving-quiet', name: 'Quiet Receiving', focus: 'catching', equipment: 'ball',
    positions: ['C'], work: '3 rounds of 20',
    how: [
      'Catch balls off the wall with as little body movement as possible.',
      'Have someone watch, or film it, and count how often your head moves.',
      'Aim for a completely still head.',
    ],
    cue: 'A quiet catcher makes borderline pitches look like strikes.',
  },

  // ---------------------------------------------------------------- speed
  {
    id: 'home-to-first', name: 'Home to First', focus: 'speed', equipment: 'field',
    positions: ['all'], work: '6 runs with full rest',
    how: [
      'Start in your stance, take a swing, then sprint through the base.',
      'Run through it, never slow down or leap at it.',
      'Time yourself and track the number.',
    ],
    cue: 'Run through the bag. Every single time.',
  },
  {
    id: 'lead-off', name: 'Lead and Break', focus: 'speed', equipment: 'none',
    positions: ['all'], work: '4 rounds of 8',
    how: [
      'Take your lead with short shuffle steps, weight balanced.',
      'On your own signal, crossover and sprint five metres.',
      'Practise getting back to the bag as well as going forward.',
    ],
    cue: 'Balanced lead. Leaning tells everyone what you will do.',
  },
  {
    id: 'sprint-starts-bb', name: 'Explosive Starts', focus: 'speed', equipment: 'none',
    positions: ['all'], work: '6 starts, walk back between',
    how: [
      'From a standing lean, let yourself fall forward then sprint ten metres.',
      'Stay low for the first five steps.',
      'Walk back to recover fully.',
    ],
    cue: 'Fall, then run. Do not step until gravity makes you.',
  },
  {
    id: 'rounding-bases', name: 'Rounding a Base', focus: 'speed', equipment: 'field',
    positions: ['all'], work: '6 repetitions',
    how: [
      'Sprint towards the bag, then flare out slightly so you can cut the corner.',
      'Hit the inside corner of the bag with your foot.',
      'Accelerate out of the turn.',
    ],
    cue: 'Bank into the turn. Running square loses a full step.',
  },
  {
    id: 'sliding-form', name: 'Sliding Form', focus: 'speed', equipment: 'field',
    positions: ['all'], work: '3 rounds of 5',
    setup: 'Wet grass or a slide mat. Never concrete or dirt without pads.',
    how: [
      'Start at a jog, drop onto your back side with one leg tucked under.',
      'Keep your hands up and off the ground.',
      'Build speed only once the form is safe.',
    ],
    cue: 'Hands up. Most sliding injuries are wrists and fingers.',
  },
  {
    id: 'shuttle-bb', name: 'Shuttle Runs', focus: 'speed', equipment: 'none',
    positions: ['all'], work: '6 rounds with 45 seconds rest',
    setup: 'Markers at ten and twenty metres.',
    how: [
      'Sprint to the first marker and back, then the second and back.',
      'Touch each line with your hand.',
      'Stay low through every turn.',
    ],
    cue: 'The turns are the work.',
  },
  {
    id: 'reaction-jump-bb', name: 'Reaction Steps', focus: 'speed', equipment: 'none',
    positions: ['all'], work: '4 rounds of 8',
    how: [
      'Stand in an athletic stance with your eyes closed.',
      'Open them and immediately sprint in the first direction you decide.',
      'Alternate directions across the round.',
    ],
    cue: 'React and go. Hesitation costs more than slow feet.',
  },

  // ---------------------------------------------------------------- power
  {
    id: 'med-ball-rotation', name: 'Rotational Throw', focus: 'power', equipment: 'gym',
    positions: ['all'], work: '4 sets of 6 each side',
    how: [
      'Stand side on to a wall holding a medicine ball at chest height.',
      'Rotate through your hips and throw the ball into the wall.',
      'Catch the rebound and reset your stance.',
    ],
    cue: 'Power comes from the hips. The arms only carry it.',
  },
  {
    id: 'broad-jump-bb', name: 'Standing Broad Jump', focus: 'power', equipment: 'none',
    positions: ['all'], work: '5 jumps with full rest',
    how: [
      'Swing the arms back, dip the hips, jump forward as far as you can.',
      'Land on both feet with bent knees.',
      'Hold the landing still.',
    ],
    cue: 'Stick the landing or it does not count.',
  },
  {
    id: 'split-squat-bb', name: 'Rear Foot Elevated Split Squat', focus: 'power',
    equipment: 'none', positions: ['all'], work: '3 sets of 8 each leg',
    setup: 'A bench or step for the back foot.',
    how: [
      'Rest the top of the back foot on the step behind you.',
      'Lower until the front thigh is level with the ground.',
      'Drive up through the front heel.',
    ],
    cue: 'Front shin upright, hips square.',
  },
  {
    id: 'hip-bridge-bb', name: 'Single Leg Hip Bridge', focus: 'power', equipment: 'none',
    positions: ['all'], work: '3 sets of 10 each side',
    how: [
      'Lie on your back, one foot planted, other leg straight.',
      'Drive the hips up through the planted heel.',
      'Lower slowly.',
    ],
    cue: 'Squeeze the glute. Do not arch the back.',
  },
  {
    id: 'wrist-forearm', name: 'Wrist and Forearm Work', focus: 'power', equipment: 'gym',
    positions: ['all'], work: '3 sets of 15 each way',
    how: [
      'With a light weight, curl the wrist up and lower it slowly.',
      'Then turn the palm down and repeat.',
      'Finish by squeezing a ball for thirty seconds.',
    ],
    cue: 'Bat control lives in the forearms.',
  },
  {
    id: 'nordic-bb', name: 'Assisted Hamstring Lower', focus: 'power', equipment: 'none',
    positions: ['all'], work: '3 sets of 5',
    setup: 'Something to hook your heels under, and a cushion for the knees.',
    how: [
      'Kneel with heels held, body straight from knee to head.',
      'Lower forward as slowly as you can.',
      'Catch yourself with your hands and push back up.',
    ],
    cue: 'Fight the fall. Slow is the point.',
  },
  {
    id: 'trap-bar-bb', name: 'Trap Bar Deadlift', focus: 'power', equipment: 'gym',
    positions: ['all'], work: '4 sets of 5',
    how: [
      'Stand inside the bar, feet hip width, chest tall, back flat.',
      'Push the floor away and stand up, then lower under control.',
      'Use a weight you could manage for eight.',
    ],
    cue: 'Form over weight. Have a coach watch this one.',
  },

  // --------------------------------------------------------- conditioning
  {
    id: 'sprint-intervals-bb', name: 'Sprint Intervals', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '10 rounds',
    how: [
      'Sprint hard for eight seconds, about the length of a play.',
      'Rest thirty seconds.',
      'Keep the last sprint as fast as the first.',
    ],
    cue: 'Baseball is short bursts. Train the real shape.',
  },
  {
    id: 'tempo-run-bb', name: 'Tempo Runs', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '8 runs of 100 metres, walking back',
    how: [
      'Run each one at about seventy percent, smooth and relaxed.',
      'Walk back slowly as the rest.',
      'Keep every run within a second or two of the others.',
    ],
    cue: 'Smooth beats fast here.',
  },
  {
    id: 'shoulder-warmup-bb', name: 'Throwing Warm Up', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, before every session',
    how: [
      'Arm circles forward and back, small building to large.',
      'Cross body swings, then slow overhead reaches.',
      'Finish with ten easy short throws before anything harder.',
    ],
    cue: 'Never throw hard cold. Not once, not ever.',
  },
  {
    id: 'core-plank-bb', name: 'Plank Series', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '3 rounds',
    how: [
      'Front plank 30 seconds, then each side for 20 seconds.',
      'Straight line heel to head, hips level.',
      'Breathe normally.',
    ],
    cue: 'Squeeze the glutes. A sagging plank does nothing.',
  },
  {
    id: 'hip-mobility-bb', name: 'Hip and Thoracic Mobility', focus: 'conditioning',
    equipment: 'none', positions: ['all'], work: '5 minutes',
    how: [
      'Leg swings forward and sideways, ten each way.',
      'Deep squat hold for thirty seconds.',
      'Finish with ten slow trunk rotations each direction.',
    ],
    cue: 'Rotation needs mobile hips and a mobile upper back.',
  },
  {
    id: 'cooldown-bb', name: 'Cool Down and Breathe', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, every session',
    how: [
      'Walk easily for three minutes until your breathing settles.',
      'Then breathe in for four seconds and out for six, for two minutes.',
      'Drink water while you do it.',
    ],
    cue: 'The session is not over until your heart rate is down.',
  },
];
