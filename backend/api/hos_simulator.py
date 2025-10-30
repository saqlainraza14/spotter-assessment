# backend/api/hos_simulator.py

import math
from datetime import datetime, timedelta

# Define driver status constants based on the logbook image and video
STATUS_OFF_DUTY = "OFF_DUTY" # Line 1
STATUS_SLEEPER = "SLEEPER"     # Line 2
STATUS_DRIVING = "DRIVING"     # Line 3
STATUS_ON_DUTY = "ON_DUTY"     # Line 4 (Not Driving)

class HOSSimulator:
    """
    Simulates a driver's trip, enforcing HOS rules and adding required stops.

    HOS Rules Based on Assessment:
    - 70 hours in 8 days (rolling)
    - 11 hours driving limit (per 14-hour shift)
    - 14 hours on-duty limit (per shift)
    - 10 hours off-duty/sleeper to reset a shift
    - 30-minute break after 8 hours of *driving*

    Trip Assumptions:
    - 1 hour for pickup
    - 1 hour for drop-off
    - Fuel stop (assuming 1 hour, 'ON_DUTY') every 1000 miles
    """

    def __init__(self, cycle_used_hours):
        # Shift Clocks (in minutes)
        self.shift_drive_remaining = 11 * 60  # 11 hours
        self.shift_on_duty_remaining = 14 * 60 # 14 hours
        self.time_until_30_min_break = 8 * 60   # 8 hours
        
        # Cycle Clock (in minutes)
        # 70 hours / 8 days
        self.cycle_remaining = (70 * 60) - (cycle_used_hours * 60)
        
        # This list will be our main output
        self.log_events = []
        # We start by assuming the driver is 'OFF_DUTY'
        # before starting the trip.
        self.current_status = STATUS_OFF_DUTY
        self.total_miles_driven = 0

    def add_log_event(self, status, duration_minutes, remarks=""):
        """Helper function to add an event to our log."""
        if duration_minutes <= 0:
            return
            
        # Add to the log
        self.log_events.append({
            "status": status,
            "duration_minutes": duration_minutes,
            "remarks": remarks
        })
        
        # Update cycle time. Driving and On-Duty count against the 70-hr clock.
        if status == STATUS_DRIVING or status == STATUS_ON_DUTY:
            self.cycle_remaining -= duration_minutes
            
        # Update shift on-duty clock
        if status == STATUS_DRIVING or status == STATUS_ON_DUTY:
            self.shift_on_duty_remaining -= duration_minutes

        # Update driving clocks
        if status == STATUS_DRIVING:
            self.shift_drive_remaining -= duration_minutes
            self.time_until_30_min_break -= duration_minutes
            
        self.current_status = status

    def take_10_hour_reset(self):
        """Simulates a full 10-hour break to reset shift clocks."""
        self.add_log_event(STATUS_OFF_DUTY, 10 * 60, "10-hour reset")
        
        # Reset shift clocks
        self.shift_drive_remaining = 11 * 60
        self.shift_on_duty_remaining = 14 * 60
        self.time_until_30_min_break = 8 * 60

    def take_30_minute_break(self):
        """Simulates the mandatory 30-minute break."""
        self.add_log_event(STATUS_OFF_DUTY, 30, "30-minute break")
        
        # Reset 30-min break clock
        self.time_until_30_min_break = 8 * 60

    def simulate_trip(self, total_drive_minutes, total_miles):
        """
        Main simulation logic. Processes the entire trip from start to finish.
        """
        
        # --- 1. Start of Trip: Pickup ---
        # Assumption: 1 hour for pickup
        self.add_log_event(STATUS_ON_DUTY, 60, "Pre-trip Inspection & Pickup")

        # --- 2. Main Driving Loop ---
        drive_time_remaining = total_drive_minutes
        miles_remaining = total_miles
        miles_since_fuel = 0

        # ---!! START FIX: Handle ZeroDivisionError !!---
        # Calculate average MPH, ensuring we don't divide by zero
        if total_drive_minutes > 0:
            avg_mph = total_miles / (total_drive_minutes / 60)
        else:
            avg_mph = 0 # Assume 0 MPH if drive time is 0
        # ---!! END FIX !!---

        while drive_time_remaining > 0:
            # Check if we have enough time in our cycle and shift
            if self.cycle_remaining <= 0 or self.shift_on_duty_remaining <= 0:
                self.take_10_hour_reset()

            if self.shift_drive_remaining <= 0:
                self.take_10_hour_reset()
                
            if self.time_until_30_min_break <= 0:
                self.take_30_minute_break()

            max_drive_segment = min(
                drive_time_remaining,
                self.shift_drive_remaining,
                self.shift_on_duty_remaining,
                self.time_until_30_min_break
            )
            
            # ---!! START FIX: Handle ZeroDivisionError !!---
            if avg_mph > 0:
                miles_in_this_segment = max_drive_segment / 60 * avg_mph
                
                if (miles_since_fuel + miles_in_this_segment) >= 1000:
                    miles_to_fuel_stop = 1000 - miles_since_fuel
                    time_to_fuel_stop_min = (miles_to_fuel_stop / avg_mph) * 60
                    
                    if time_to_fuel_stop_min < max_drive_segment:
                        max_drive_segment = time_to_fuel_stop_min
                    
                    self.add_log_event(STATUS_DRIVING, max_drive_segment, "Driving")
                    drive_time_remaining -= max_drive_segment
                    miles_driven = (max_drive_segment / 60) * avg_mph
                    miles_remaining -= miles_driven
                    self.total_miles_driven += miles_driven
                    
                    self.add_log_event(STATUS_ON_DUTY, 60, "Fueling")
                    miles_since_fuel = 0 
                    continue 

            # ---!! END FIX !!---

            # --- No fuel stop, just drive ---
            self.add_log_event(STATUS_DRIVING, max_drive_segment, "Driving")
            drive_time_remaining -= max_drive_segment
            
            if avg_mph > 0:
                miles_driven = (max_drive_segment / 60) * avg_mph
                miles_remaining -= miles_driven
                self.total_miles_driven += miles_driven
                miles_since_fuel += miles_driven

        # --- 3. End of Trip: Drop-off ---
        self.add_log_event(STATUS_ON_DUTY, 60, "Post-trip Inspection & Drop-off")
        
        # --- 4. Finalize Log ---
        self.add_log_event(STATUS_OFF_DUTY, 0, "End of Trip")
        
        return self.generate_daily_logs()

    def generate_daily_logs(self):
        """
        Converts the continuous list of events into
        one or more 24-hour (1440 minute) logbook days.
        """
        logs_by_day = []
        
        time_in_day = 0
        events_for_this_day = []
        
        for event in self.log_events:
            duration = event['duration_minutes']
            while duration > 0:
                # How much time is left in this 24-hour day?
                time_left_in_day = 1440 - time_in_day
                
                if duration <= time_left_in_day:
                    # Event fits completely in this day
                    events_for_this_day.append({
                        "status": event['status'],
                        "duration_minutes": duration,
                        "remarks": event['remarks']
                    })
                    time_in_day += duration
                    duration = 0 # Event is done
                else:
                    # Event spills into the next day
                    if time_left_in_day > 0:
                        events_for_this_day.append({
                            "status": event['status'],
                            "duration_minutes": time_left_in_day,
                            "remarks": event['remarks']
                        })
                    
                    # This day is full
                    if events_for_this_day:
                        logs_by_day.append(events_for_this_day)
                    
                    # Start a new day
                    events_for_this_day = []
                    time_in_day = 0
                    duration -= time_left_in_day # Remainder goes to next day
        
        # Add the last day
        if events_for_this_day:
            logs_by_day.append(events_for_this_day)

        return {
            "total_miles": self.total_miles_driven,
            "cycle_remaining_hours": self.cycle_remaining / 60,
            "daily_logs": logs_by_day
        }