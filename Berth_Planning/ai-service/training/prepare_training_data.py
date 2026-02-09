"""
SmartBerth AI - Training Data Preparation for Qwen3 Fine-Tuning
Converts CSV training datasets into instruction-tuning format (JSONL)

This script processes the training database and generates:
1. Domain knowledge Q&A pairs
2. Berth allocation decision scenarios
3. ETA prediction examples
4. Constraint validation cases
5. Vessel/Port information queries
"""

import pandas as pd
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths - relative to ai-service folder
SCRIPT_DIR = Path(__file__).parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
TRAIN_DATA_DIR = AI_SERVICE_DIR / "Train_Database"
OUTPUT_DIR = SCRIPT_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

# System prompt for SmartBerth AI
SYSTEM_PROMPT = """You are SmartBerth AI, an intelligent assistant specialized in port berth planning and optimization. You provide accurate, data-driven insights about vessel operations, berth allocation, ETA predictions, and maritime logistics. Always be precise with measurements and timings."""


def load_datasets() -> Dict[str, pd.DataFrame]:
    """Load all training CSV files"""
    datasets = {}
    csv_files = {
        'ports': 'SmartBerth_AI_Port_Parameters_Training_Data.csv',
        'terminals': 'SmartBerth_AI_Terminal_Parameters_Training_Data.csv',
        'berths': 'SmartBerth_AI_Berth_Parameters_Training_Data.csv',
        'vessels': 'SmartBerth_AI_Vessel_Parameters_Training_Data.csv',
        'vessel_calls': 'SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv',
        'ais': 'SmartBerth_AI_AIS_Parameters_Training_Data.csv',
        'weather': 'SmartBerth_AI_Weather_Parameters_Training_Data.csv',
        'pilots': 'SmartBerth_AI_Pilotage_Parameters_Training_Data.csv',
        'tugs': 'SmartBerth_AI_Tugboat_Parameters_Training_Data.csv',
        'channels': 'SmartBerth_AI_Channel_Parameters_Training_Data.csv',
        'ukc': 'SmartBerth_AI_UKC_Training_Data.csv',
        'anchorages': 'SmartBerth_AI_Anchorage_Parameters_Training_Data.csv',
    }
    
    for name, filename in csv_files.items():
        filepath = TRAIN_DATA_DIR / filename
        if filepath.exists():
            datasets[name] = pd.read_csv(filepath)
            logger.info(f"Loaded {name}: {len(datasets[name])} records")
        else:
            logger.warning(f"File not found: {filepath}")
    
    return datasets


def generate_port_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate Q&A pairs about ports"""
    examples = []
    ports = datasets.get('ports', pd.DataFrame())
    
    for _, port in ports.iterrows():
        # Port information query
        examples.append({
            "instruction": f"Tell me about the port {port['portName']} ({port['portCode']}).",
            "input": "",
            "output": f"{port['portName']} (Code: {port['portCode']}) is located in {port['city']}, {port['country']}. "
                     f"It operates in timezone {port['timezone']} at coordinates ({port['latitude']}, {port['longitude']}). "
                     f"The port is {'currently active' if port['isActive'] else 'inactive'} and can be contacted at {port['contactEmail']}."
        })
        
        # Location query
        examples.append({
            "instruction": f"What is the location of port code {port['portCode']}?",
            "input": "",
            "output": f"Port {port['portCode']} ({port['portName']}) is located at latitude {port['latitude']} and longitude {port['longitude']} in {port['city']}, {port['country']}."
        })
    
    return examples


def generate_berth_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate Q&A pairs about berths and terminals"""
    examples = []
    berths = datasets.get('berths', pd.DataFrame())
    terminals = datasets.get('terminals', pd.DataFrame())
    
    # Sample berths for training (to avoid too many similar examples)
    sample_berths = berths.sample(min(500, len(berths))) if len(berths) > 500 else berths
    
    for _, berth in sample_berths.iterrows():
        # Berth specifications
        examples.append({
            "instruction": f"What are the specifications of berth {berth['berthCode']}?",
            "input": "",
            "output": f"Berth {berth['berthCode']} ({berth['berthName']}) at port {berth['portCode']} has the following specifications:\n"
                     f"- Length: {berth['length']}m\n"
                     f"- Depth: {berth['depth']}m\n"
                     f"- Max Draft: {berth['maxDraft']}m\n"
                     f"- Max LOA: {berth['maxLOA']}m\n"
                     f"- Max Beam: {berth['maxBeam']}m\n"
                     f"- Type: {berth['berthType']}\n"
                     f"- Cranes: {berth['numberOfCranes']}\n"
                     f"- Status: {'Active' if berth['isActive'] else 'Inactive'}"
        })
        
        # Vessel fit check
        test_loa = random.randint(150, 400)
        test_draft = round(random.uniform(8, 20), 1)
        can_fit = test_loa <= berth['maxLOA'] and test_draft <= berth['maxDraft']
        
        examples.append({
            "instruction": f"Can a vessel with LOA {test_loa}m and draft {test_draft}m berth at {berth['berthCode']}?",
            "input": "",
            "output": f"{'Yes' if can_fit else 'No'}, a vessel with LOA {test_loa}m and draft {test_draft}m "
                     f"{'can' if can_fit else 'cannot'} berth at {berth['berthCode']}. "
                     f"The berth has maximum LOA of {berth['maxLOA']}m and maximum draft of {berth['maxDraft']}m. "
                     f"{'All constraints are satisfied.' if can_fit else 'The vessel exceeds ' + ('LOA' if test_loa > berth['maxLOA'] else 'draft') + ' limits.'}"
        })
    
    return examples


def generate_vessel_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate Q&A pairs about vessels"""
    examples = []
    vessels = datasets.get('vessels', pd.DataFrame())
    
    # Sample vessels
    sample_vessels = vessels.sample(min(500, len(vessels))) if len(vessels) > 500 else vessels
    
    for _, vessel in sample_vessels.iterrows():
        examples.append({
            "instruction": f"What are the specifications of vessel {vessel['vessel_name']} (IMO: {vessel['imo_number']})?",
            "input": "",
            "output": f"Vessel {vessel['vessel_name']} (IMO: {vessel['imo_number']}) specifications:\n"
                     f"- Type: {vessel['vessel_type']}\n"
                     f"- Flag: {vessel['flagStateName']} ({vessel['flagState']})\n"
                     f"- LOA: {vessel['loa']}m\n"
                     f"- Beam: {vessel['beam']}m\n"
                     f"- Draft: {vessel['draft']}m\n"
                     f"- Gross Tonnage: {vessel['grossTonnage']} GT\n"
                     f"- Cargo Type: {vessel['cargoType']}\n"
                     f"- Cargo Volume: {vessel['cargoVolume']} {vessel['cargoUnit']}"
        })
        
        # Vessel type query
        examples.append({
            "instruction": f"What type of vessel is {vessel['vessel_name']}?",
            "input": "",
            "output": f"{vessel['vessel_name']} is a {vessel['vessel_type']} vessel with a gross tonnage of {vessel['grossTonnage']} GT. "
                     f"It is registered under the {vessel['flagStateName']} flag and primarily carries {vessel['cargoType']}."
        })
    
    return examples


def generate_vessel_call_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate Q&A pairs about vessel calls and berth assignments"""
    examples = []
    calls = datasets.get('vessel_calls', pd.DataFrame())
    
    # Sample vessel calls
    sample_calls = calls.sample(min(1000, len(calls))) if len(calls) > 1000 else calls
    
    for _, call in sample_calls.iterrows():
        # ETA variance analysis
        eta_variance = call.get('etaVarianceHours', 0)
        variance_status = "on time" if abs(eta_variance) < 1 else ("early" if eta_variance < 0 else "late")
        
        examples.append({
            "instruction": f"Tell me about the vessel call for {call['vesselName']} at port {call['portCode']}.",
            "input": "",
            "output": f"Vessel {call['vesselName']} (IMO: {call['imoNumber']}) made a call at port {call['portCode']}:\n"
                     f"- Vessel Type: {call['vesselType']}\n"
                     f"- Dimensions: LOA {call['loa']}m, Beam {call['beam']}m\n"
                     f"- Arrival Draft: {call['arrivalDraft']}m, Departure Draft: {call['departureDraft']}m\n"
                     f"- Initial ETA: {call['etaInitial']}\n"
                     f"- Updated ETA: {call['etaUpdated']}\n"
                     f"- Actual Arrival (ATA): {call['ata']}\n"
                     f"- ETA Variance: {eta_variance:.1f} hours ({variance_status})\n"
                     f"- Assigned Berth: {call['berthCode']} ({call['berthName']})\n"
                     f"- Dwell Time: {call['dwellTimeHours']:.1f} hours\n"
                     f"- Cargo: {call['cargoQuantity']} {call['cargoUnit']} of {call['cargoType']} ({call['cargoOperation']})\n"
                     f"- Call Status: {call['callStatus']}"
        })
        
        # Waiting time analysis
        waiting_time = call.get('waitingTimeHours', 0)
        if waiting_time > 0:
            examples.append({
                "instruction": f"Why did vessel {call['vesselName']} have to wait {waiting_time:.1f} hours at port {call['portCode']}?",
                "input": "",
                "output": f"Vessel {call['vesselName']} waited {waiting_time:.1f} hours at {call['portCode']} before berthing. "
                         f"The vessel arrived at {call['ata']} and was assigned to berth {call['berthCode']}. "
                         f"Berthing delay was {call.get('berthingDelayMins', 0)} minutes. "
                         f"Factors may include berth availability, pilot/tug scheduling, or tidal window constraints. "
                         f"{call.get('tugsAssigned', 0)} tugs and {call.get('pilotsAssigned', 0)} pilots were assigned for this operation."
            })
        
        # Berth assignment reasoning
        examples.append({
            "instruction": f"Why was berth {call['berthCode']} assigned to {call['vesselName']}?",
            "input": "",
            "output": f"Berth {call['berthCode']} ({call['berthName']}) was assigned to {call['vesselName']} because:\n"
                     f"1. Terminal Type Match: The berth is a {call['terminalType']} terminal suitable for {call['vesselType']} vessels\n"
                     f"2. Cargo Compatibility: The berth handles {call['cargoType']} cargo operations\n"
                     f"3. Vessel Dimensions: The vessel (LOA: {call['loa']}m, Beam: {call['beam']}m, Draft: {call['arrivalDraft']}m) fits within berth limits\n"
                     f"4. Operation Type: The berth supports {call['cargoOperation']} operations\n"
                     f"The assignment achieved a dwell time of {call['dwellTimeHours']:.1f} hours for {call['cargoQuantity']} {call['cargoUnit']} of cargo."
        })
    
    return examples


def generate_eta_prediction_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate ETA prediction training examples"""
    examples = []
    ais = datasets.get('ais', pd.DataFrame())
    calls = datasets.get('vessel_calls', pd.DataFrame())
    
    # Sample AIS records
    sample_ais = ais.sample(min(2000, len(ais))) if len(ais) > 2000 else ais
    
    for _, record in sample_ais.iterrows():
        # ETA from AIS data
        examples.append({
            "instruction": f"Based on AIS data, what is the predicted ETA for vessel ID {record['vesselId']} approaching port {record['portCode']}?",
            "input": f"Current position: ({record['latitude']}, {record['longitude']}), Speed: {record['speed']} knots, Course: {record['course']}°, Distance to port: {record['distanceToPort']} NM, Phase: {record['phase']}",
            "output": f"Based on the AIS data, the vessel is currently in the {record['phase']} phase, "
                     f"approximately {record['distanceToPort']:.1f} nautical miles from port {record['portCode']}. "
                     f"Traveling at {record['speed']} knots with course {record['course']}°, "
                     f"the estimated time to port is approximately {record['timeToPort']:.0f} minutes. "
                     f"The vessel's navigation status is '{record['navigationStatus']}'. "
                     f"Expected ETA: {record['eta']}"
        })
    
    # ETA variance examples from vessel calls
    sample_calls = calls.sample(min(500, len(calls))) if len(calls) > 500 else calls
    
    for _, call in sample_calls.iterrows():
        variance = call.get('etaVarianceHours', 0)
        if abs(variance) > 0.5:  # Only significant variances
            examples.append({
                "instruction": f"Analyze the ETA prediction accuracy for {call['vesselName']} at {call['portCode']}.",
                "input": f"Initial ETA: {call['etaInitial']}, Updated ETA: {call['etaUpdated']}, Actual Arrival: {call['ata']}",
                "output": f"ETA Analysis for {call['vesselName']}:\n"
                         f"- Initial ETA: {call['etaInitial']}\n"
                         f"- Updated ETA: {call['etaUpdated']}\n"
                         f"- Actual Arrival: {call['ata']}\n"
                         f"- Variance: {variance:.2f} hours ({'late' if variance > 0 else 'early'})\n"
                         f"- Berthing Delay: {call.get('berthingDelayMins', 0)} minutes\n\n"
                         f"The vessel arrived {abs(variance):.1f} hours {'later' if variance > 0 else 'earlier'} than predicted. "
                         f"{'This delay may be attributed to weather conditions, port congestion, or vessel operational issues.' if variance > 0 else 'The vessel made good progress and arrived ahead of schedule.'}"
            })
    
    return examples


def generate_weather_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate weather-related Q&A pairs"""
    examples = []
    weather = datasets.get('weather', pd.DataFrame())
    
    # Sample weather records
    sample_weather = weather.sample(min(500, len(weather))) if len(weather) > 500 else weather
    
    for _, record in sample_weather.iterrows():
        # Weather conditions
        examples.append({
            "instruction": f"What are the weather conditions at port {record['portCode']} on {record['recordedAt']}?",
            "input": "",
            "output": f"Weather conditions at {record['portCode']} ({record['recordedAt']}):\n"
                     f"- Condition: {record['weatherCondition']}\n"
                     f"- Wind: {record['windSpeed']} knots from {record['windDirection']}\n"
                     f"- Visibility: {record['visibility']}m\n"
                     f"- Wave Height: {record['waveHeight']}m\n"
                     f"- Temperature: {record['temperature']}°C\n"
                     f"- Precipitation: {record['precipitation']}\n"
                     f"- Weather Alert: {'Yes' if record['isAlert'] else 'No'}\n"
                     f"- Season: {record['season'].capitalize()}"
        })
        
        # Berthing safety check
        is_safe = record['windSpeed'] < 25 and record['waveHeight'] < 2.0 and record['visibility'] > 1000
        examples.append({
            "instruction": f"Is it safe for berthing operations at {record['portCode']} given current weather?",
            "input": f"Wind: {record['windSpeed']} knots, Waves: {record['waveHeight']}m, Visibility: {record['visibility']}m",
            "output": f"{'Yes, berthing operations can proceed' if is_safe else 'Caution advised for berthing operations'} at {record['portCode']}.\n"
                     f"Current conditions: Wind {record['windSpeed']} knots (limit: 25 knots), "
                     f"Wave height {record['waveHeight']}m (limit: 2.0m), "
                     f"Visibility {record['visibility']}m (minimum: 1000m).\n"
                     f"{'All parameters are within safe limits.' if is_safe else 'One or more parameters exceed safe operating limits. Consider delay or enhanced precautions.'}"
        })
    
    return examples


def generate_ukc_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate UKC (Under Keel Clearance) training examples"""
    examples = []
    ukc = datasets.get('ukc', pd.DataFrame())
    
    for _, record in ukc.iterrows():
        examples.append({
            "instruction": f"Calculate the UKC requirements for a {record['vesselType']} vessel transiting the channel.",
            "input": f"Vessel: {record['vesselType']}, LOA: {record['vesselLOA']}m, Beam: {record['vesselBeam']}m, Static Draft: {record['vesselStaticDraft']}m, Transit Speed: {record['transitSpeed']} knots, Cargo: {record['cargoType']} ({record['cargoCondition']})",
            "output": f"UKC Calculation for {record['vesselType']} ({record['cargoType']}):\n\n"
                     f"**Vessel Parameters:**\n"
                     f"- LOA: {record['vesselLOA']}m, Beam: {record['vesselBeam']}m\n"
                     f"- Block Coefficient: {record['blockCoefficient']}\n"
                     f"- Static Draft: {record['vesselStaticDraft']}m\n"
                     f"- Dynamic Draft: {record['vesselDynamicDraft']}m\n"
                     f"- Transit Speed: {record['transitSpeed']} knots\n\n"
                     f"**Allowances:**\n"
                     f"- Squat Allowance: {record['squatAllowance']}m\n"
                     f"- Heel Allowance: {record['heelAllowance']}m\n"
                     f"- Wave Response: {record['waveResponseAllowance']}m\n"
                     f"- Safety Margin: {record['safetyMargin']}m\n"
                     f"- Total Allowances: {record['totalAllowances']}m\n\n"
                     f"**Channel/Berth:**\n"
                     f"- Channel Depth at Tide: {record['channelDepthAtTide']}m\n"
                     f"- Berth Depth at Tide: {record['berthDepthAtTide']}m\n"
                     f"- Tide Height: {record['tideHeight']}m\n"
                     f"- Wave Condition: {record['waveCondition']} ({record['waveHeight']}m)\n\n"
                     f"**Result:**\n"
                     f"- Required UKC: {record['requiredUKC']}m ({record['requiredUKCSpec']})\n"
                     f"- Calculated UKC: {record['calculatedUKC']}m\n"
                     f"- UKC Margin: {record['ukcMargin']}m\n"
                     f"- **Status: {record['ukcStatus']}**\n"
                     f"- Optimal Transit Time: {record['optimalTransitTime']}\n"
                     f"- Confined Water: {'Yes' if record['isConfined'] else 'No'}"
        })
    
    return examples


def generate_pilot_tug_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate pilot and tug resource Q&A pairs"""
    examples = []
    pilots = datasets.get('pilots', pd.DataFrame())
    tugs = datasets.get('tugs', pd.DataFrame())
    
    # Pilot queries
    sample_pilots = pilots.sample(min(200, len(pilots))) if len(pilots) > 200 else pilots
    for _, pilot in sample_pilots.iterrows():
        examples.append({
            "instruction": f"Can pilot {pilot['pilotName']} handle a {pilot['maxVesselGT']} GT vessel at night in adverse weather?",
            "input": "",
            "output": f"Pilot {pilot['pilotName']} ({pilot['pilotCode']}) at {pilot['portName']}:\n"
                     f"- Pilot Type: {pilot['pilotType']}, Class: {pilot['pilotClass']}\n"
                     f"- Certification Level: {pilot['certificationLevel']}\n"
                     f"- Experience: {pilot['experienceYears']} years\n"
                     f"- Max Vessel: {pilot['maxVesselGT']} GT, {pilot['maxVesselLOA']}m LOA\n"
                     f"- Night Operations: {'Certified' if pilot['nightOperations'] else 'Not certified'}\n"
                     f"- Adverse Weather: {'Certified' if pilot['adverseWeather'] else 'Not certified'}\n"
                     f"- Languages: {pilot['languages']}\n"
                     f"- Status: {pilot['status']}\n\n"
                     f"{'This pilot CAN handle night operations in adverse weather.' if pilot['nightOperations'] and pilot['adverseWeather'] else 'This pilot has LIMITATIONS for night/adverse weather operations.'}"
        })
    
    # Tug queries
    sample_tugs = tugs.sample(min(200, len(tugs))) if len(tugs) > 200 else tugs
    for _, tug in sample_tugs.iterrows():
        examples.append({
            "instruction": f"What are the capabilities of tugboat {tug['tugName']} at port {tug['portCode']}?",
            "input": "",
            "output": f"Tugboat {tug['tugName']} ({tug['tugCode']}) specifications:\n"
                     f"- Type: {tug['tugTypeFullName']} ({tug['tugClass']})\n"
                     f"- Operator: {tug['operator']}\n"
                     f"- Bollard Pull: {tug['bollardPull']} tonnes\n"
                     f"- Dimensions: {tug['length']}m x {tug['beam']}m x {tug['draft']}m\n"
                     f"- Engine Power: {tug['enginePower']} kW\n"
                     f"- Max Speed: {tug['maxSpeed']} knots\n"
                     f"- Year Built: {tug['yearBuilt']}\n"
                     f"- FiFi Class: {tug['fifiClass']}\n"
                     f"- Winch Capacity: {tug['winchCapacity']} tonnes\n"
                     f"- Crew: {tug['crewSize']}\n"
                     f"- Status: {tug['status']}"
        })
    
    return examples


def generate_constraint_qa(datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Generate constraint validation Q&A pairs"""
    examples = []
    vessels = datasets.get('vessels', pd.DataFrame())
    berths = datasets.get('berths', pd.DataFrame())
    
    # Cross-check vessels against berths
    sample_vessels = vessels.sample(min(200, len(vessels))) if len(vessels) > 200 else vessels
    sample_berths = berths.sample(min(200, len(berths))) if len(berths) > 200 else berths
    
    for _, vessel in sample_vessels.iterrows():
        for _, berth in sample_berths.sample(min(3, len(sample_berths))).iterrows():
            loa_ok = vessel['loa'] <= berth['maxLOA']
            beam_ok = vessel['beam'] <= berth['maxBeam']
            draft_ok = vessel['draft'] <= berth['maxDraft']
            all_ok = loa_ok and beam_ok and draft_ok
            
            violations = []
            if not loa_ok:
                violations.append(f"LOA ({vessel['loa']}m > {berth['maxLOA']}m)")
            if not beam_ok:
                violations.append(f"Beam ({vessel['beam']}m > {berth['maxBeam']}m)")
            if not draft_ok:
                violations.append(f"Draft ({vessel['draft']}m > {berth['maxDraft']}m)")
            
            examples.append({
                "instruction": f"Check if vessel {vessel['vessel_name']} can be allocated to berth {berth['berthCode']}.",
                "input": f"Vessel: LOA {vessel['loa']}m, Beam {vessel['beam']}m, Draft {vessel['draft']}m. Berth limits: Max LOA {berth['maxLOA']}m, Max Beam {berth['maxBeam']}m, Max Draft {berth['maxDraft']}m",
                "output": f"Constraint Check: {vessel['vessel_name']} → {berth['berthCode']}\n\n"
                         f"**Vessel Dimensions:**\n"
                         f"- LOA: {vessel['loa']}m {'✓' if loa_ok else '✗'} (limit: {berth['maxLOA']}m)\n"
                         f"- Beam: {vessel['beam']}m {'✓' if beam_ok else '✗'} (limit: {berth['maxBeam']}m)\n"
                         f"- Draft: {vessel['draft']}m {'✓' if draft_ok else '✗'} (limit: {berth['maxDraft']}m)\n\n"
                         f"**Result: {'FEASIBLE - All constraints satisfied' if all_ok else 'NOT FEASIBLE - Violations: ' + ', '.join(violations)}**"
            })
    
    return examples


def generate_domain_knowledge_qa() -> List[Dict]:
    """Generate general domain knowledge Q&A pairs from the PRD"""
    examples = [
        {
            "instruction": "What is the purpose of SmartBerth AI?",
            "input": "",
            "output": "SmartBerth AI is an AI-powered berth planning and allocation system that enables Terminal Operators to:\n\n1. **Proactively plan berth schedules** based on predicted ETAs\n2. **Dynamically re-optimize berth allocation** in response to delays and disruptions\n3. **Improve operational efficiency** and decision-making through data-driven recommendations\n\nThe system integrates with Port Community Systems (PCS) and Maritime Single Window (MSW) platforms to optimize berth allocation, predict vessel arrival times, and streamline cargo operations."
        },
        {
            "instruction": "What are the hard constraints for berth allocation?",
            "input": "",
            "output": "Hard constraints for berth allocation are non-negotiable requirements that must be satisfied:\n\n1. **Physical Compatibility:**\n   - Vessel LOA must not exceed berth maximum LOA\n   - Vessel beam must not exceed berth maximum beam\n   - Vessel draft must not exceed berth water depth\n\n2. **Cargo Type Compatibility:**\n   - Container vessels → Container terminals only\n   - Bulk carriers → Bulk terminals or multipurpose berths\n   - Tankers → Liquid cargo berths with safety equipment\n   - RoRo vessels → RoRo terminals with ramps\n\n3. **Equipment Availability:**\n   - Required cranes must be operational\n   - Specialized handling equipment available\n\n4. **Tidal Restrictions:**\n   - Vessel must meet UKC requirements for the tidal window\n\nNo berth assignment is allowed if any hard constraint is violated."
        },
        {
            "instruction": "How does ETA prediction work in SmartBerth AI?",
            "input": "",
            "output": "SmartBerth AI predicts vessel ETA using multiple data sources:\n\n**Data Inputs:**\n1. **Historical Data:** Past arrival/departure patterns for similar vessels\n2. **AIS Movement Data:** Real-time position, speed, and course\n3. **Weather Data:** Wind, waves, visibility affecting transit\n4. **Tidal Data:** Tidal windows affecting approach timing\n5. **Port Congestion:** Current queue and berth utilization\n\n**Prediction Process:**\n1. Ingest real-time AIS position and speed\n2. Calculate distance to port and expected transit time\n3. Apply weather impact adjustments\n4. Consider historical patterns for vessel type\n5. Factor in port congestion delays\n\n**Outputs:**\n- Predicted ETA (vs declared ETA)\n- Expected delay in minutes\n- Confidence score (0-100%)\n\nThe model updates dynamically as new data arrives, providing 24-hour advance detection of delays."
        },
        {
            "instruction": "What factors determine vessel readiness for berthing?",
            "input": "",
            "output": "Vessel readiness for berthing is determined by:\n\n**1. Pilot Availability:**\n- Certified pilot for vessel size and type\n- Night/adverse weather qualification if applicable\n\n**2. Tug Availability:**\n- Sufficient bollard pull for vessel GT\n- Required number of tugs based on vessel size\n\n**3. Tidal Window:**\n- UKC requirements met for current/predicted tide\n- Safe transit depth through channel\n\n**4. Regulatory Clearance:**\n- Immigration/customs clearance status\n- Port health clearance\n- Security clearance\n\n**Readiness Status:**\n- **Ready:** All requirements satisfied\n- **At Risk:** One or more factors uncertain\n- **Not Ready:** Clear blocker identified\n\nReadiness prediction precision target is ≥80% with false 'Ready' predictions <10%."
        },
        {
            "instruction": "What is UKC and why is it important?",
            "input": "",
            "output": "**Under Keel Clearance (UKC)** is the minimum distance between a vessel's keel (bottom) and the seabed during transit or berthing.\n\n**Why It's Critical:**\n- Prevents grounding accidents\n- Ensures safe navigation in channels\n- Required for port entry approval\n\n**UKC Calculation Components:**\n1. **Static Draft:** Vessel draft at rest\n2. **Dynamic Draft:** Includes squat effect at speed\n3. **Squat Allowance:** Draft increase due to vessel speed\n4. **Heel Allowance:** Roll and pitch effects\n5. **Wave Response:** Vertical movement from waves\n6. **Safety Margin:** Additional buffer\n\n**Factors Considered:**\n- Tide height (affects available depth)\n- Wave conditions\n- Channel depth\n- Vessel block coefficient\n- Transit speed\n\n**UKC Status:**\n- **Safe:** Adequate margin above requirements\n- **Marginal:** Within limits but minimal margin\n- **Unsafe:** Requirements not met - transit not permitted"
        },
        {
            "instruction": "How does SmartBerth AI handle conflicts?",
            "input": "",
            "output": "SmartBerth AI detects and resolves scheduling conflicts through:\n\n**Conflict Types Detected:**\n1. **Berth Overlaps:** Two vessels scheduled at same berth/time\n2. **Resource Clashes:** Insufficient pilots/tugs for simultaneous operations\n3. **Tidal Window Conflicts:** Multiple vessels needing same tidal window\n\n**Detection Process:**\n- Continuous monitoring of schedule\n- Automatic alert when conflict identified\n- Severity classification (Low/Medium/High)\n\n**Resolution Options:**\n- AI generates multiple resolution alternatives\n- Each option shows trade-offs and impacts\n- Options ranked by optimization criteria\n\n**Resolution Criteria:**\n- Minimize cascading delays\n- Prioritize high-priority vessels\n- Maximize berth utilization\n- Respect all hard constraints\n\n**Operator Workflow:**\n- System presents Before vs After comparison\n- Operator approval required before changes applied\n- Full audit trail maintained"
        },
        {
            "instruction": "What is the vessel call workflow from arrival to departure?",
            "input": "",
            "output": "**Complete Vessel Call Workflow:**\n\n**Phase 1: Pre-Arrival (72-24 hours before)**\n- Shipping agent declares ETA, cargo, crew via PCS/MSW\n- FAL forms submitted\n- Pilot/tug services requested\n\n**Phase 2: AI Processing**\n- SmartBerth ingests PCS/MSW data\n- AIS integration for real-time tracking\n- Weather/tidal analysis\n- UKC calculation\n- Berth allocation optimization\n- Resource scheduling (pilots, tugs)\n\n**Phase 3: Confirmation**\n- Berth plan published to terminal\n- Terminal prepares (yard, cranes, labor)\n\n**Phase 4: Arrival Operations**\n- Vessel arrives at anchorage (if needed)\n- Pilot boards at pilot station\n- Tug escort to berth\n- First line → All fast → Cargo starts\n\n**Phase 5: Cargo Operations**\n- Cargo discharge/loading\n- Real-time progress monitoring\n\n**Phase 6: Departure**\n- Cargo complete\n- Pilot/tug coordination\n- Vessel departure (ATD recorded)\n\n**Timestamps Captured:**\nETA → ATA → Pilot Boarding → First Line → All Fast → Cargo Start → Cargo Complete → ETD → ATD"
        }
    ]
    
    return examples


def convert_to_chat_format(examples: List[Dict]) -> List[Dict]:
    """Convert instruction-input-output format to chat format for Qwen3"""
    chat_examples = []
    
    for ex in examples:
        # Create chat format
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # User message
        user_content = ex["instruction"]
        if ex.get("input"):
            user_content += f"\n\n{ex['input']}"
        messages.append({"role": "user", "content": user_content})
        
        # Assistant response
        messages.append({"role": "assistant", "content": ex["output"]})
        
        chat_examples.append({"messages": messages})
    
    return chat_examples


def save_training_data(examples: List[Dict], filename: str):
    """Save training data in JSONL format"""
    output_path = OUTPUT_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(examples)} examples to {output_path}")
    return output_path


def main():
    """Main function to generate all training data"""
    logger.info("Starting training data preparation...")
    
    # Load datasets
    datasets = load_datasets()
    
    # Generate Q&A pairs from each data source
    all_examples = []
    
    logger.info("Generating port Q&A pairs...")
    all_examples.extend(generate_port_qa(datasets))
    
    logger.info("Generating berth Q&A pairs...")
    all_examples.extend(generate_berth_qa(datasets))
    
    logger.info("Generating vessel Q&A pairs...")
    all_examples.extend(generate_vessel_qa(datasets))
    
    logger.info("Generating vessel call Q&A pairs...")
    all_examples.extend(generate_vessel_call_qa(datasets))
    
    logger.info("Generating ETA prediction Q&A pairs...")
    all_examples.extend(generate_eta_prediction_qa(datasets))
    
    logger.info("Generating weather Q&A pairs...")
    all_examples.extend(generate_weather_qa(datasets))
    
    logger.info("Generating UKC Q&A pairs...")
    all_examples.extend(generate_ukc_qa(datasets))
    
    logger.info("Generating pilot/tug Q&A pairs...")
    all_examples.extend(generate_pilot_tug_qa(datasets))
    
    logger.info("Generating constraint validation Q&A pairs...")
    all_examples.extend(generate_constraint_qa(datasets))
    
    logger.info("Generating domain knowledge Q&A pairs...")
    all_examples.extend(generate_domain_knowledge_qa())
    
    # Shuffle examples
    random.shuffle(all_examples)
    
    logger.info(f"Total training examples generated: {len(all_examples)}")
    
    # Split into train/validation sets (90/10)
    split_idx = int(len(all_examples) * 0.9)
    train_examples = all_examples[:split_idx]
    val_examples = all_examples[split_idx:]
    
    # Convert to chat format
    train_chat = convert_to_chat_format(train_examples)
    val_chat = convert_to_chat_format(val_examples)
    
    # Save in multiple formats
    # 1. Instruction format (for reference)
    save_training_data(train_examples, "train_instructions.jsonl")
    save_training_data(val_examples, "val_instructions.jsonl")
    
    # 2. Chat format (for Qwen3 fine-tuning)
    save_training_data(train_chat, "train_chat.jsonl")
    save_training_data(val_chat, "val_chat.jsonl")
    
    # 3. Combined dataset info
    dataset_info = {
        "created_at": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "sources": list(datasets.keys()),
        "source_records": {k: len(v) for k, v in datasets.items()}
    }
    
    with open(OUTPUT_DIR / "dataset_info.json", 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    logger.info("Training data preparation complete!")
    logger.info(f"Train: {len(train_examples)} examples")
    logger.info(f"Val: {len(val_examples)} examples")
    
    return all_examples


if __name__ == "__main__":
    main()
