// Rinkcraft drill library. Built for off-ice work you can do alone.
//
// equipment is the MINIMUM needed:
//   none  -> open space            stick -> stick and a ball
//   pad   -> shooting pad and net  ice   -> supervised ice time
//   gym   -> rink plus a weight room

export type Focus =
  | 'stickhandling' | 'shooting' | 'passing' | 'skating'
  | 'agility' | 'power' | 'goalie' | 'conditioning';

export type Equipment = 'none' | 'stick' | 'pad' | 'ice' | 'gym';

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
  // -------------------------------------------------------- stickhandling
  {
    id: 'stationary-toe-drag', name: 'Stationary Puck Handling', focus: 'stickhandling',
    equipment: 'stick', positions: ['C', 'W', 'D'], work: '4 rounds of 45 seconds',
    how: [
      'Stand with the ball in front of you and move it side to side with soft hands.',
      'Keep the ball in the middle of the blade and cushion it on every touch.',
      'Look up at a point on the wall, not down at the ball.',
    ],
    cue: 'Soft hands, quiet blade, eyes up.',
  },
  {
    id: 'wide-handles', name: 'Wide Handles', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W'], work: '4 rounds of 30 seconds',
    how: [
      'Move the ball as far to each side as you can reach without moving your feet.',
      'Roll your wrists over the ball to keep it covered.',
      'Gradually go wider and faster.',
    ],
    cue: 'Reach wide. Narrow hands get stripped.',
  },
  {
    id: 'figure-eight', name: 'Figure Eight', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 45 seconds',
    setup: 'Two markers about a metre apart.',
    how: [
      'Weave the ball around both markers in a figure eight.',
      'Keep your feet still and let the stick do the work.',
      'Reverse direction halfway through the round.',
    ],
    cue: 'Control the ball at the tip of the blade.',
  },
  {
    id: 'toe-drag-pull', name: 'Toe Drag', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W'], work: '3 rounds of 20 each side',
    how: [
      'Push the ball out in front, then catch it with the toe of the blade.',
      'Drag it back across your body in one motion.',
      'Finish in control, ready to shoot.',
    ],
    cue: 'Reach, catch, pull. One movement.',
  },
  {
    id: 'one-hand-carry', name: 'One Hand Carry', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W'], work: '3 rounds of 30 seconds each hand',
    how: [
      'Hold the stick with the top hand only and carry the ball forward.',
      'Protect it with your body as if someone is beside you.',
      'Keep your head up the whole time.',
    ],
    cue: 'Top hand strong. Extend and protect.',
  },
  {
    id: 'obstacle-weave', name: 'Obstacle Weave', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '6 trips through',
    setup: 'Five markers in a line, a metre apart.',
    how: [
      'Walk through the markers, taking the ball around each one.',
      'Once smooth, do it at a jog.',
      'Accelerate out of the last marker for five metres.',
    ],
    cue: 'Smooth first, fast second.',
  },
  {
    id: 'quick-hands', name: 'Quick Hands Burst', focus: 'stickhandling', equipment: 'stick',
    positions: ['C', 'W'], work: '5 rounds of 15 seconds',
    how: [
      'Move the ball side to side as fast as you possibly can.',
      'Keep every touch on the blade, not scraping the ground.',
      'Rest thirty seconds between rounds.',
    ],
    cue: 'Fast but clean. Sloppy speed is not speed.',
  },

  // -------------------------------------------------------------- shooting
  {
    id: 'wrist-shot-form', name: 'Wrist Shot Form', focus: 'shooting', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '4 rounds of 15',
    how: [
      'Start with the ball behind your back foot on the pad.',
      'Sweep it forward, shifting your weight from back foot to front.',
      'Roll the wrists at the end and finish with the blade pointing at the target.',
    ],
    cue: 'Weight transfer first. The arms finish it, they do not start it.',
  },
  {
    id: 'snap-shot', name: 'Snap Shot', focus: 'shooting', equipment: 'stick',
    positions: ['C', 'W'], work: '4 rounds of 15',
    how: [
      'Keep the ball beside your front foot with no windup.',
      'Load the stick by pressing down into it, then release fast.',
      'Aim to get it away quicker than a wrist shot, not harder.',
    ],
    cue: 'No backswing. Loading the stick is the power.',
  },
  {
    id: 'target-corners', name: 'Corner Targets', focus: 'shooting', equipment: 'pad',
    positions: ['C', 'W', 'D'], work: '5 shots at each of 4 corners',
    setup: 'Mark four corners on your net.',
    how: [
      'Call the corner out loud before every shot.',
      'Score a point for each one you hit.',
      'Write the score down and beat it next session.',
    ],
    cue: 'Pick a corner, not the net.',
  },
  {
    id: 'quick-release', name: 'Quick Release', focus: 'shooting', equipment: 'pad',
    positions: ['C', 'W'], work: '4 rounds of 10',
    how: [
      'Start with your back to the net, ball on the pad.',
      'Turn, find the ball and shoot in one motion.',
      'Time yourself from turn to shot and try to shorten it.',
    ],
    cue: 'The fastest shot beats the hardest one.',
  },
  {
    id: 'backhand', name: 'Backhand Shot', focus: 'shooting', equipment: 'stick',
    positions: ['C', 'W'], work: '3 rounds of 12',
    how: [
      'Cup the ball on the backhand side of the blade.',
      'Sweep through, lifting with the wrists at the end.',
      'Follow through high to lift it.',
    ],
    cue: 'Cup it and lift. Do not slap at it.',
  },
  {
    id: 'one-timer-setup', name: 'One Timer Setup', focus: 'shooting', equipment: 'pad',
    positions: ['C', 'W', 'D'], work: '3 rounds of 10',
    how: [
      'Roll the ball across yourself, then shoot it without stopping it first.',
      'Open your hips to the net before the ball arrives.',
      'Keep the blade low and closed over the ball.',
    ],
    cue: 'Be ready early. The ball should never wait for you.',
  },
  {
    id: 'shot-volume', name: 'Shot Volume Set', focus: 'shooting', equipment: 'pad',
    positions: ['C', 'W', 'D'], work: '100 shots across the session',
    how: [
      'Mix wrist, snap and backhand shots.',
      'Take them in sets of twenty with a short rest between.',
      'Stop early if your form falls apart. Volume with bad form builds bad habits.',
    ],
    cue: 'Reps build the shot. Form decides which shot you build.',
  },

  // --------------------------------------------------------------- passing
  {
    id: 'wall-pass-hockey', name: 'Wall Passing', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '4 rounds of 30 passes',
    setup: 'A flat wall or a rebounder, three metres away.',
    how: [
      'Pass the ball into the wall and receive the return.',
      'Cushion each return by giving with the blade rather than blocking it.',
      'Keep the passes flat and on the blade.',
    ],
    cue: 'Catch it soft, send it hard.',
  },
  {
    id: 'saucer-pass', name: 'Saucer Pass', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 15',
    setup: 'Something low to pass over, and a target beyond it.',
    how: [
      'Roll the ball from heel to toe of the blade and lift it as you release.',
      'Make it land flat and settle quickly.',
      'Clear the obstacle without sending it high.',
    ],
    cue: 'Heel to toe, low flight, flat landing.',
  },
  {
    id: 'backhand-pass', name: 'Backhand Pass', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 20',
    how: [
      'Pass off your backhand into the wall.',
      'Keep the blade square and follow through at the target.',
      'Receive the return on your forehand, then repeat.',
    ],
    cue: 'Backhand passes win games. Practise them like forehands.',
  },
  {
    id: 'one-touch', name: 'One Touch Passing', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W'], work: '4 rounds of 20',
    how: [
      'Pass into the wall and return the rebound without stopping it.',
      'Stay light on your feet and move to the ball.',
      'Build speed as it gets comfortable.',
    ],
    cue: 'Blade square before the ball arrives.',
  },
  {
    id: 'pass-under-pressure', name: 'Pass on the Move', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 12',
    how: [
      'Carry the ball a few strides, then pass into the wall without stopping.',
      'Receive the return still moving.',
      'Never plant your feet to make the pass.',
    ],
    cue: 'Pass in stride. Stopping tells everyone what you are doing.',
  },
  {
    id: 'receive-bad-pass', name: 'Bad Pass Reception', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 15',
    how: [
      'Throw the ball off the wall at awkward angles, behind you and into your feet.',
      'Settle whatever comes back and get it under control quickly.',
      'Accept the misses.',
    ],
    cue: 'Most passes you get will be bad. Train for those.',
  },
  {
    id: 'head-up-pass', name: 'Head Up Passing', focus: 'passing', equipment: 'stick',
    positions: ['C', 'W', 'D'], work: '3 rounds of 20',
    how: [
      'Put a number or word on the wall above your target.',
      'Read it out loud on every pass.',
      'If you cannot read it, your head is down.',
    ],
    cue: 'Feel the ball, see the ice.',
  },

  // --------------------------------------------------------------- skating
  {
    id: 'skating-stance', name: 'Skating Stance Hold', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '3 rounds of 40 seconds',
    how: [
      'Bend your knees deeply, chest up, back flat, hands in front.',
      'Your knees should hide your toes when you look down.',
      'Hold and breathe normally.',
    ],
    cue: 'Deep knees, tall chest. Power comes from the bend.',
  },
  {
    id: 'stride-extension', name: 'Stride Extension', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '3 rounds of 12 each leg',
    how: [
      'From a low stance, push one leg out sideways and back until it is straight.',
      'Hold the full extension for a beat, then recover under your body.',
      'Keep your chest and hips facing forward.',
    ],
    cue: 'Push out and back, not down. Finish the stride.',
  },
  {
    id: 'lateral-slide', name: 'Slide Board Shuffle', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '4 rounds of 30 seconds',
    setup: 'A smooth floor in socks, or a slide board if you have one.',
    how: [
      'Push side to side in a low stance, gliding on each foot.',
      'Stay low the whole time and keep your chest up.',
      'Make each push long rather than quick.',
    ],
    cue: 'Long glides. This is the closest thing to ice off the ice.',
  },
  {
    id: 'crossover-steps', name: 'Crossover Steps', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '4 rounds of 10 each direction',
    setup: 'Mark a circle about three metres across.',
    how: [
      'Walk the circle crossing one foot over the other, staying low.',
      'Push with the outside leg on every crossover.',
      'Build to a jog once the pattern is clean.',
    ],
    cue: 'Cross over and push. Do not just step around.',
  },
  {
    id: 'edge-balance', name: 'Single Leg Balance', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '3 rounds of 30 seconds each leg',
    how: [
      'Stand on one leg in a quarter squat, other knee raised.',
      'Hold still, then close your eyes for the last ten seconds.',
      'Keep the standing knee bent, never locked.',
    ],
    cue: 'Balance on the ice is balance off it.',
  },
  {
    id: 'ice-edges', name: 'Edge Work on Ice', focus: 'skating', equipment: 'ice',
    positions: ['all'], work: '10 minutes of a supervised session',
    how: [
      'Skate slow circles on inside edges, then outside edges, both directions.',
      'Stay low and let the edge carry you rather than taking extra strides.',
      'Do this at a supervised session, never alone.',
    ],
    cue: 'Slow and deep beats fast and upright.',
  },
  {
    id: 'start-steps', name: 'Explosive Starts', focus: 'skating', equipment: 'none',
    positions: ['all'], work: '6 starts with full rest',
    how: [
      'From a low stance, take three hard running steps with your feet turned out.',
      'Drive the arms and stay low for all three.',
      'Walk back and reset fully.',
    ],
    cue: 'First three steps win the race to the puck.',
  },

  // --------------------------------------------------------------- agility
  {
    id: 'lateral-bound-hockey', name: 'Skater Bounds', focus: 'agility', equipment: 'none',
    positions: ['all'], work: '4 sets of 8 each side',
    how: [
      'Push off one leg sideways and land balanced on the other.',
      'Hold each landing for a beat before pushing back.',
      'Cover as much ground as you can control.',
    ],
    cue: 'Stick every landing. This is the skating stride on land.',
  },
  {
    id: 'quick-feet-ladder', name: 'Quick Feet Pattern', focus: 'agility', equipment: 'none',
    positions: ['all'], work: '4 rounds of 20 seconds',
    setup: 'A line on the ground, or a ladder if you have one.',
    how: [
      'Step both feet over the line and back as fast as you can.',
      'Stay on the balls of your feet and keep contacts quiet.',
      'Repeat facing sideways for the last two rounds.',
    ],
    cue: 'Quiet feet. Noise means you are landing heavy.',
  },
  {
    id: 'pivot-drill', name: 'Pivot and Go', focus: 'agility', equipment: 'none',
    positions: ['D', 'C'], work: '4 rounds of 8',
    how: [
      'Backpedal three steps, pivot hard and sprint forward five.',
      'Alternate pivoting over each shoulder.',
      'Stay low through the turn.',
    ],
    cue: 'Turn the hips, the feet follow.',
  },
  {
    id: 'cone-cuts', name: 'Tight Cuts', focus: 'agility', equipment: 'none',
    positions: ['C', 'W'], work: '6 trips',
    setup: 'Five markers in a zigzag, three metres apart.',
    how: [
      'Sprint the pattern, planting the outside foot to change direction.',
      'Keep your shoulders low and your chest up.',
      'Accelerate out of the last marker.',
    ],
    cue: 'Plant outside, push inside.',
  },
  {
    id: 'reaction-turn-hockey', name: 'Blind Turn and Go', focus: 'agility', equipment: 'none',
    positions: ['all'], work: '8 repetitions',
    how: [
      'Stand facing away with your eyes closed.',
      'Count three, open your eyes, turn and sprint ten metres.',
      'Alternate turning each way.',
    ],
    cue: 'Balance first, then speed.',
  },
  {
    id: 'stop-start', name: 'Stop and Start', focus: 'agility', equipment: 'none',
    positions: ['all'], work: '4 rounds of 6',
    how: [
      'Sprint five metres, stop dead under control, then sprint back.',
      'Drop your hips to stop rather than stiffening your legs.',
      'Every stop should be silent and balanced.',
    ],
    cue: 'Stopping well is a skill. Train it like one.',
  },
  {
    id: 'shuffle-square-hockey', name: 'Shuffle Squares', focus: 'agility', equipment: 'none',
    positions: ['D', 'G'], work: '4 laps each direction',
    setup: 'Four markers in a square, four metres a side.',
    how: [
      'Shuffle one side, backpedal the next, shuffle, sprint the last.',
      'Never cross your feet on the shuffles.',
      'Stay low the whole lap.',
    ],
    cue: 'Low and square. Standing up is losing.',
  },

  // ----------------------------------------------------------------- power
  {
    id: 'squat-jump-hockey', name: 'Countermovement Jump', focus: 'power', equipment: 'none',
    positions: ['all'], work: '4 rounds of 5',
    how: [
      'Dip quickly to a quarter squat, then jump as high as you can.',
      'Land softly and reset fully before the next.',
      'Rest a minute between rounds.',
    ],
    cue: 'The dip and the jump are one movement.',
  },
  {
    id: 'split-squat-hockey', name: 'Rear Foot Elevated Split Squat', focus: 'power',
    equipment: 'none', positions: ['all'], work: '3 sets of 8 each leg',
    setup: 'A bench or step for the back foot.',
    how: [
      'Rest the top of the back foot on the step behind you.',
      'Lower until the front thigh is level with the ground.',
      'Drive up through the front heel.',
    ],
    cue: 'Hockey is a one leg sport. Train one leg at a time.',
  },
  {
    id: 'lateral-lunge', name: 'Lateral Lunge', focus: 'power', equipment: 'none',
    positions: ['all'], work: '3 sets of 10 each side',
    how: [
      'Step wide to one side and sit into that hip, keeping the other leg straight.',
      'Keep both feet flat and your chest up.',
      'Push back to the middle.',
    ],
    cue: 'Sit into the hip. This is where the stride comes from.',
  },
  {
    id: 'hip-bridge-hockey', name: 'Single Leg Hip Bridge', focus: 'power', equipment: 'none',
    positions: ['all'], work: '3 sets of 10 each side',
    how: [
      'Lie on your back, one foot planted, the other leg straight out.',
      'Drive the hips up through the planted heel.',
      'Lower slowly under control.',
    ],
    cue: 'Squeeze the glute at the top. No arching the back.',
  },
  {
    id: 'core-rotation', name: 'Rotational Core', focus: 'power', equipment: 'gym',
    positions: ['all'], work: '3 sets of 10 each way',
    how: [
      'Hold a medicine ball at chest height in a half kneeling position.',
      'Rotate through the torso and throw the ball into a wall.',
      'Catch it and reset without losing your posture.',
    ],
    cue: 'Shots come from rotation. Build it here.',
  },
  {
    id: 'nordic-hockey', name: 'Assisted Hamstring Lower', focus: 'power', equipment: 'none',
    positions: ['all'], work: '3 sets of 5',
    setup: 'Something solid to hook your heels under, and a cushion for the knees.',
    how: [
      'Kneel with heels held, body straight from knee to head.',
      'Lower forward as slowly as you can.',
      'Catch yourself with your hands and push back up.',
    ],
    cue: 'Fight the fall. Slow is the whole point.',
  },
  {
    id: 'trap-bar-hockey', name: 'Trap Bar Deadlift', focus: 'power', equipment: 'gym',
    positions: ['all'], work: '4 sets of 5',
    how: [
      'Stand inside the bar, feet hip width, chest tall and back flat.',
      'Push the floor away and stand up, then lower under control.',
      'Use a weight you could manage for eight.',
    ],
    cue: 'Never chase weight over form. Have a coach watch this one.',
  },

  // --------------------------------------------------------------- goalie
  {
    id: 'butterfly-drop', name: 'Butterfly Drop', focus: 'goalie', equipment: 'none',
    positions: ['G'], work: '4 rounds of 10',
    setup: 'Do this on a soft surface or with knee pads on.',
    how: [
      'From your stance, drop to both knees with the pads flaring out.',
      'Keep your chest tall and your hands in front, not on the floor.',
      'Push back up to your stance without using your hands.',
    ],
    cue: 'Chest up. Dropping is not collapsing.',
  },
  {
    id: 'goalie-shuffle', name: 'Post to Post Shuffle', focus: 'goalie', equipment: 'none',
    positions: ['G'], work: '4 rounds of 8',
    setup: 'Mark two posts about two metres apart.',
    how: [
      'Shuffle from one post to the other in your stance.',
      'Stay square and never cross your feet.',
      'Stop balanced at each post before going back.',
    ],
    cue: 'Square, still, then set. In that order.',
  },
  {
    id: 'glove-hand', name: 'Glove Hand Reactions', focus: 'goalie', equipment: 'stick',
    positions: ['G'], work: '4 rounds of 20',
    setup: 'A wall and a tennis ball.',
    how: [
      'Throw the ball off the wall and catch it in your glove hand.',
      'Vary the height and angle so you never know what is coming.',
      'Catch it, do not trap it against your body.',
    ],
    cue: 'Take it out of the air. Hands lead the body.',
  },
  {
    id: 'tracking', name: 'Puck Tracking', focus: 'goalie', equipment: 'stick',
    positions: ['G'], work: '3 rounds of 20',
    how: [
      'Throw the ball off the wall and follow it all the way into your hands with your eyes.',
      'Turn your head, not just your eyes.',
      'Say "see it" out loud on every rep until it is automatic.',
    ],
    cue: 'You cannot stop what you did not see.',
  },
  {
    id: 'recovery-push', name: 'Recovery Push', focus: 'goalie', equipment: 'none',
    positions: ['G'], work: '3 rounds of 8 each side',
    how: [
      'Drop to butterfly, then push off the inside edge of one knee to move sideways.',
      'Come back up to your stance immediately.',
      'Alternate directions.',
    ],
    cue: 'Down, across, up. Never stay down.',
  },
  {
    id: 'goalie-conditioning', name: 'Crease Intervals', focus: 'goalie', equipment: 'none',
    positions: ['G'], work: '8 rounds',
    how: [
      'Work fifteen seconds: shuffles, drops, recoveries, in any order.',
      'Rest twenty seconds.',
      'Keep your stance the whole working period.',
    ],
    cue: 'Tired goalies stand up. Train so you do not.',
  },

  // --------------------------------------------------------- conditioning
  {
    id: 'shift-intervals', name: 'Shift Intervals', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '8 rounds',
    how: [
      'Work hard for 40 seconds, roughly the length of a shift.',
      'Rest 80 seconds, like sitting on the bench.',
      'Mix sprints, bounds and quick feet in the working period.',
    ],
    cue: 'Train the shape of the game, not just fitness.',
  },
  {
    id: 'suicides', name: 'Line Sprints', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '6 rounds with 60 seconds rest',
    setup: 'Four markers at increasing distances.',
    how: [
      'Sprint to the first and back, second and back, and so on.',
      'Touch every line with your hand.',
      'Keep the times even across all six rounds.',
    ],
    cue: 'Do not win the first and die on the last.',
  },
  {
    id: 'bike-intervals', name: 'Bike or Run Intervals', focus: 'conditioning', equipment: 'gym',
    positions: ['all'], work: '10 rounds of 30 seconds',
    how: [
      'Go hard for thirty seconds, then easy for ninety.',
      'Hold the same output on the last round as the first.',
      'Stop the session if the output drops badly.',
    ],
    cue: 'Consistency across rounds beats one heroic effort.',
  },
  {
    id: 'core-plank-hockey', name: 'Plank Series', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '3 rounds',
    how: [
      'Hold a front plank 30 seconds, then each side 20 seconds.',
      'Straight line from heel to head, hips level.',
      'Breathe normally throughout.',
    ],
    cue: 'Squeeze the glutes. A sagging plank does nothing.',
  },
  {
    id: 'hip-mobility', name: 'Hip Opener Warm Up', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, before every session',
    how: [
      'Leg swings forward and back, then side to side, ten each way.',
      'Deep squat hold for thirty seconds.',
      'Finish with slow lunges with a twist.',
    ],
    cue: 'Hockey lives in the hips. Open them before you load them.',
  },
  {
    id: 'cooldown-hockey', name: 'Cool Down and Breathe', focus: 'conditioning', equipment: 'none',
    positions: ['all'], work: '5 minutes, every session',
    how: [
      'Walk easily for three minutes until your breathing settles.',
      'Then breathe in for four seconds and out for six, for two minutes.',
      'Drink water while you do it.',
    ],
    cue: 'The session is not over until your heart rate is down.',
  },
];
