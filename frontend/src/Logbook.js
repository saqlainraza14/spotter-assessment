// frontend/src/Logbook.js

import React, { useRef, useEffect }from 'react';

// Status-to-Row mapping (Line 1, 2, 3, 4)
const STATUS_ROWS = {
  OFF_DUTY: 68, // Y-pixel coordinate for Line 1
  SLEEPER: 98,  // Y-pixel coordinate for Line 2
  DRIVING: 128, // Y-pixel coordinate for Line 3
  ON_DUTY: 158, // Y-pixel coordinate for Line 4
};

// These are pixel coordinates I measured from the image
const GRID_START_X = 54;
const GRID_END_X = 878;
const GRID_WIDTH = GRID_END_X - GRID_START_X;
const MINUTES_PER_DAY = 1440; // 24 * 60

const Logbook = ({ dayNumber, events, tripSummary }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2;
    ctx.strokeStyle = 'blue';

    let currentX = GRID_START_X;
    let totalMinutes = 0;
    
    let totalOffDuty = 0;
    let totalSleeper = 0;
    let totalDriving = 0;
    let totalOnDuty = 0;

    events.forEach((event, index) => {
      // Calculate times for the recap box
      if (event.status === 'OFF_DUTY') totalOffDuty += event.duration_minutes;
      if (event.status === 'SLEEPER') totalSleeper += event.duration_minutes;
      if (event.status === 'DRIVING') totalDriving += event.duration_minutes;
      if (event.status === 'ON_DUTY') totalOnDuty += event.duration_minutes;

      // --- Draw the lines ---
      const y = STATUS_ROWS[event.status];
      const eventWidth = (event.duration_minutes / MINUTES_PER_DAY) * GRID_WIDTH;
      
      ctx.beginPath();
      ctx.moveTo(currentX, y);
      ctx.lineTo(currentX + eventWidth, y);
      ctx.stroke();
      
      // Draw vertical line for status change
      if (index > 0) {
        const prevY = STATUS_ROWS[events[index-1].status];
        ctx.beginPath();
        ctx.moveTo(currentX, prevY);
        ctx.lineTo(currentX, y);
        ctx.stroke();
      }
      
      totalMinutes += event.duration_minutes;
      currentX = GRID_START_X + (totalMinutes / MINUTES_PER_DAY) * GRID_WIDTH;
    });
    
    // --- Fill text fields ---
    ctx.fillStyle = 'black';
    ctx.font = '14px Arial';

    // Total Miles (only on day 1 for this sim)
    if (dayNumber === 1) {
      ctx.fillText(Math.round(tripSummary.total_miles), 105, 175);
    }
    
    // Total hours per line
    const toHours = (min) => (min / 60).toFixed(1);
    ctx.fillText(toHours(totalOffDuty), 895, 68);
    ctx.fillText(toHours(totalSleeper), 895, 98);
    ctx.fillText(toHours(totalDriving), 895, 128);
    ctx.fillText(toHours(totalOnDuty), 895, 158);
    
    // Recap
    const drivingAndOnDuty = toHours(totalDriving + totalOnDuty);
    ctx.fillText(drivingAndOnDuty, 115, 620); // A. Total hours
    ctx.fillText('70', 215, 620); // B. Total hours last 7 days
    
    // C. Total hours available
    const available = (tripSummary.cycle_remaining_hours).toFixed(1);
    ctx.fillText(available, 310, 620); 

  }, [events, tripSummary, dayNumber]);

  return (
    <div className="logbook-wrapper">
      <h4>Day {dayNumber}</h4>
      <canvas
        ref={canvasRef}
        width={950} // Image dimensions
        height={734} // Image dimensions
        style={{ backgroundImage: 'url(/blank-paper-log.png)' }}
      />
    </div>
  );
};

export default Logbook;