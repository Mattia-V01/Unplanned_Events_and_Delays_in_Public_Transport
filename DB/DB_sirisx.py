import os
import requests
import sqlite3
import xml.etree.ElementTree as ET
import schedule
import time
from datetime import datetime

# API Configuration
URL = "https://api.opentransportdata.swiss/la/siri-sx"
KEY = "YOUR KEY"

# Database path
DB_PATH = "c:/Tesi/Daten/data/situations_sirisx.sqlite"

# XML Namespace
namespace = {
    'siri': 'http://www.siri.org.uk/siri',
    'ns1': 'http://www.siri.org.uk/siri'
}
ET.register_namespace("", namespace["siri"])

# Create the database folder if it does not exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Function to set up the database and tables
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: Situations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Situations (
            SituationID TEXT PRIMARY KEY,
            SituationNumber TEXT,
            CreationTime TEXT,
            CountryRef TEXT,
            ParticipantRef TEXT,
            Version INTEGER,
            Source_Type TEXT,
            Source_Name TEXT,
            VersionedAtTime TEXT,
            Progress TEXT,
            Validity_Start TEXT,
            Validity_End TEXT,
            Publication_Start TEXT,
            Publication_End TEXT,
            AlertCause TEXT,
            Priority INTEGER,
            ScopeType TEXT,
            Language TEXT,
            Summary_DE TEXT,
            Summary_FR TEXT,
            Summary_IT TEXT,
            Summary_EN TEXT,
            Description_DE TEXT,
            Description_FR TEXT,
            Description_IT TEXT,
            Description_EN TEXT,
            Affects_StopPlace_Ref TEXT,
            Affects_StopPlace_Name TEXT,
            Affects_Facility_Ref TEXT,
            Affects_Facility_Name TEXT,
            Affects_Facility_Status TEXT,
            Conseq_Affects_StopPlace_Ref TEXT,
            Conseq_Affects_StopPlace_Name TEXT,
            Conseq_Affects_Facility_Ref TEXT,
            Conseq_Affects_Facility_Name TEXT,
            Conseq_Affects_Facility_Status TEXT,
            Publish_ScopeType TEXT,
            Publish_Affects_StopPlace_Ref TEXT,
            Publish_Affects_StopPlace_Name TEXT,
            PIA_ActionRef TEXT,
            PIA_RecordedAt TEXT,
            PIA_OwnerRef TEXT
        )
    """)
    
    # Table 2: Text_S
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Text_S (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SituationID TEXT,
            -- PIA_TextSize TEXT,  --
            PIA_Summary_DE TEXT,
            PIA_Summary_FR TEXT,
            PIA_Summary_IT TEXT,
            PIA_Summary_EN TEXT,
            PIA_Reason_DE TEXT,
            PIA_Reason_FR TEXT,
            PIA_Reason_IT TEXT,
            PIA_Reason_EN TEXT,
            PIA_Desc_DE TEXT,
            PIA_Desc_FR TEXT,
            PIA_Desc_IT TEXT,
            PIA_Desc_EN TEXT,
            PIA_Rec_DE TEXT,
            PIA_Rec_FR TEXT,
            PIA_Rec_IT TEXT,
            PIA_Rec_EN TEXT,
            PIA_Duration_DE TEXT,
            PIA_Duration_FR TEXT,
            PIA_Duration_IT TEXT,
            PIA_Duration_EN TEXT,
            FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
        )
    """)

    # Table 3: Text_M
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Text_M (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SituationID TEXT,
            -- PIA_TextSize TEXT,  --
            PIA_Summary_DE TEXT,
            PIA_Summary_FR TEXT,
            PIA_Summary_IT TEXT,
            PIA_Summary_EN TEXT,
            PIA_Reason_DE TEXT,
            PIA_Reason_FR TEXT,
            PIA_Reason_IT TEXT,
            PIA_Reason_EN TEXT,
            PIA_Desc_DE TEXT,
            PIA_Desc_FR TEXT,
            PIA_Desc_IT TEXT,
            PIA_Desc_EN TEXT,
            PIA_Rec_DE TEXT,
            PIA_Rec_FR TEXT,
            PIA_Rec_IT TEXT,
            PIA_Rec_EN TEXT,
            PIA_Duration_DE TEXT,
            PIA_Duration_FR TEXT,
            PIA_Duration_IT TEXT,
            PIA_Duration_EN TEXT,
            FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
        )
    """)

    # Table 4: Text_L
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Text_L (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SituationID TEXT,
            -- PIA_TextSize TEXT,  --
            PIA_Summary_DE TEXT,
            PIA_Summary_FR TEXT,
            PIA_Summary_IT TEXT,
            PIA_Summary_EN TEXT,
            PIA_Reason_DE TEXT,
            PIA_Reason_FR TEXT,
            PIA_Reason_IT TEXT,
            PIA_Reason_EN TEXT,
            PIA_Desc_DE TEXT,
            PIA_Desc_FR TEXT,
            PIA_Desc_IT TEXT,
            PIA_Desc_EN TEXT,
            PIA_Rec_DE TEXT,
            PIA_Rec_FR TEXT,
            PIA_Rec_IT TEXT,
            PIA_Rec_EN TEXT,
            PIA_Duration_DE TEXT,
            PIA_Duration_FR TEXT,
            PIA_Duration_IT TEXT,
            PIA_Duration_EN TEXT,
            FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
        )
    """)
    
    # Table 5: Perspective
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Perspective (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SituationID TEXT,
            PIA_Perspective TEXT,
            FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
        )
    """)

    # Table 6: StopPoints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS StopPoints (
        StopPointID INTEGER PRIMARY KEY AUTOINCREMENT,
        SituationID TEXT NOT NULL,
        StopPointRef TEXT,
        StopPointName TEXT,
        Longitude REAL,
        Latitude REAL,
        StopPlaceRef TEXT,
        StopPlaceName TEXT,
        MobilityImpairedAccess TEXT,
        WheelchairAccess TEXT,
        StepFreeAccess TEXT,
        FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
)
    """)    
    
    # Table 7: Networks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AffectedNetworks (
        NetworkID INTEGER PRIMARY KEY AUTOINCREMENT,
        SituationID TEXT NOT NULL,
        OperatorRef TEXT,
        LineRef TEXT,
        PublishedLineName TEXT,
        FOREIGN KEY (SituationID) REFERENCES Situations(SituationID)
        )
    """)

    conn.commit()
    conn.close()

# Extracts attributes and nested elements from an XML element while ensuring proper key formatting.
# def extract_nested_attributes(element, namespace, prefix=""):
#     attributes = {}

#     # Extract the element's text if available
#     element_name = element.tag.split("}")[-1]
#     if element.text and element.text.strip():
#         attributes[prefix + element_name] = element.text.strip()

#     # Extract attributes of the element
#     for attr_name, attr_value in element.attrib.items():
#         attr_name_clean = attr_name.split("}")[-1]
#         attributes[f"{prefix}{attr_name_clean}"] = attr_value.strip()

#     # Extract child elements recursively
#     for child in element:
#         child_name = child.tag.split("}")[-1]
#         new_prefix = f"{prefix}{child_name}_" if prefix else f"{child_name}_"
#         child_attributes = extract_nested_attributes(child, namespace, prefix=new_prefix)

#         # Ensure we don't duplicate the tag name at multiple levels
#         for key, value in child_attributes.items():
#             if key.startswith(new_prefix + child_name):  # Avoid double names like "Summary_Summary"
#                 new_key = key.replace(new_prefix + child_name, new_prefix[:-1], 1)
#                 attributes[new_key] = value
#             else:
#                 attributes[key] = value

#     return attributes

# Function to fetch and process XML
def fetch_and_process_xml():
    headers = {'Content-Type': 'application/xml', 'Authorization': 'Bearer ' + KEY}
    response = requests.get(URL, headers=headers)
    response.encoding = 'utf-8'
    
    if response.status_code == 200:
        process_xml(response.text)
    else:
        print(f"Failed to fetch XML: {response.status_code}")

# Function to process XML
def process_xml(xml_data):
    """ Processes the XML data and inserts it into the database. """
    tree = ET.ElementTree(ET.fromstring(xml_data))
    root = tree.getroot()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for situation in root.findall(".//siri:PtSituationElement", namespace):
        planned_element = situation.find("siri:Planned", namespace)
        if planned_element is not None and planned_element.text and planned_element.text.strip().lower() == "true":
            print("Skipping planned situation...")
            continue

        # Extract attributes for Situations table
        attributes = {
            "SituationNumber": situation.findtext("siri:SituationNumber", default=None, namespaces=namespace),
            "CreationTime": situation.findtext("siri:CreationTime", default=None, namespaces=namespace),
            "CountryRef": situation.findtext("siri:CountryRef", default=None, namespaces=namespace),
            "ParticipantRef": situation.findtext("siri:ParticipantRef", default=None, namespaces=namespace),
            "Version": situation.findtext("siri:Version", default=None, namespaces=namespace),
            "VersionedAtTime": situation.findtext("siri:VersionedAtTime", default=None, namespaces=namespace),
            "Progress": situation.findtext("siri:Progress", default=None, namespaces=namespace),
            "AlertCause": situation.findtext("siri:AlertCause", default=None, namespaces=namespace),
            "Priority": situation.findtext("siri:Priority", default=None, namespaces=namespace),
            "ScopeType": situation.findtext("siri:ScopeType", default=None, namespaces=namespace),
            "Language": situation.findtext("siri:Language", default=None, namespaces=namespace),
        }

        # Extract Source details
        source_element = situation.find("siri:Source", namespace)
        attributes["Source_Type"] = source_element.findtext("siri:SourceType", default=None, namespaces=namespace) if source_element is not None else None
        attributes["Source_Name"] = source_element.findtext("siri:Name", default=None, namespaces=namespace) if source_element is not None else None

        # Extract Validity Period
        validity_element = situation.find("siri:ValidityPeriod", namespace)
        attributes["Validity_Start"] = validity_element.findtext("siri:StartTime", default=None, namespaces=namespace) if validity_element is not None else None
        attributes["Validity_End"] = validity_element.findtext("siri:EndTime", default=None, namespaces=namespace) if validity_element is not None else None

        # Extract Publication Window
        publication_element = situation.find("siri:PublicationWindow", namespace)
        attributes["Publication_Start"] = publication_element.findtext("siri:StartTime", default=None, namespaces=namespace) if publication_element is not None else None
        attributes["Publication_End"] = publication_element.findtext("siri:EndTime", default=None, namespaces=namespace) if publication_element is not None else None

        # Extract Stop Place Affects
        affects_stop_place = situation.find(".//siri:Affects/siri:StopPlaces/siri:AffectedStopPlace", namespace)
        attributes["Affects_StopPlace_Ref"] = affects_stop_place.findtext("siri:StopPlaceRef", default=None, namespaces=namespace) if affects_stop_place is not None else None
        attributes["Affects_StopPlace_Name"] = affects_stop_place.findtext("siri:PlaceName", default=None, namespaces=namespace) if affects_stop_place is not None else None

        # Extract Facility Affects
        affects_facility = situation.find(".//siri:AffectedFacilities/siri:AffectedFacility", namespace)
        attributes["Affects_Facility_Ref"] = affects_facility.findtext("siri:FacilityRef", default=None, namespaces=namespace) if affects_facility is not None else None
        attributes["Affects_Facility_Name"] = affects_facility.findtext("siri:FacilityName", default=None, namespaces=namespace) if affects_facility is not None else None
        attributes["Affects_Facility_Status"] = affects_facility.findtext("siri:FacilityStatus", default=None, namespaces=namespace) if affects_facility is not None else None

        # Extract Consequences -> Stop Place
        conseq_stop_place = situation.find(".//siri:Consequence/siri:Affects/siri:StopPlaces/siri:AffectedStopPlace", namespace)
        attributes["Conseq_Affects_StopPlace_Ref"] = conseq_stop_place.findtext("siri:StopPlaceRef", default=None, namespaces=namespace) if conseq_stop_place is not None else None
        attributes["Conseq_Affects_StopPlace_Name"] = conseq_stop_place.findtext("siri:PlaceName", default=None, namespaces=namespace) if conseq_stop_place is not None else None

        # Extract Consequences -> Facility
        conseq_facility = situation.find(".//siri:Consequence/siri:Affects/siri:StopPlaces/siri:AffectedStopPlace/siri:AffectedFacilities/siri:AffectedFacility", namespace)
        attributes["Conseq_Affects_Facility_Ref"] = conseq_facility.findtext("siri:FacilityRef", default=None, namespaces=namespace) if conseq_facility is not None else None
        attributes["Conseq_Affects_Facility_Name"] = conseq_facility.findtext("siri:FacilityName", default=None, namespaces=namespace) if conseq_facility is not None else None
        attributes["Conseq_Affects_Facility_Status"] = conseq_facility.findtext("siri:FacilityStatus", default=None, namespaces=namespace) if conseq_facility is not None else None

        # Extract Summary and Description in multiple languages
        for summary in situation.findall("siri:Summary", namespace):
            lang = summary.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "unknown").upper()
            attributes[f"Summary_{lang}"] = summary.text.strip() if summary.text is not None else None

        for description in situation.findall("siri:Description", namespace):
            lang = description.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "unknown").upper()
            attributes[f"Description_{lang}"] = description.text.strip() if description.text is not None else None

        # Extract Publishing Actions
        publish_action = situation.find(".//siri:PublishingAction/siri:PublishAtScope", namespace)
        if publish_action is not None:
            attributes["Publish_ScopeType"] = publish_action.findtext("siri:ScopeType", default=None, namespaces=namespace)
            publish_affects_stop = publish_action.find(".//siri:AffectedStopPlace", namespace)
            if publish_affects_stop is not None:
                attributes["Publish_Affects_StopPlace_Ref"] = publish_affects_stop.findtext("siri:StopPlaceRef", default=None, namespaces=namespace)
                attributes["Publish_Affects_StopPlace_Name"] = publish_affects_stop.findtext("siri:PlaceName", default=None, namespaces=namespace)

        # Extract Passenger Information Action
        pia_action = situation.find(".//siri:PassengerInformationAction", namespace)
        if pia_action is not None:
            attributes["PIA_ActionRef"] = pia_action.findtext("siri:ActionRef", default=None, namespaces=namespace)
            attributes["PIA_RecordedAt"] = pia_action.findtext("siri:RecordedAtTime", default=None, namespaces=namespace)
            attributes["PIA_OwnerRef"] = pia_action.findtext("siri:OwnerRef", default=None, namespaces=namespace)

        # Extract Perspectives
        perspectives = [perspective.text for perspective in pia_action.findall("siri:Perspective", namespace) if perspective.text]
        attributes["PIA_Perspective"] = ", ".join(perspectives) if perspectives else None

        # Generate a unique SituationID by concatenating SituationNumber, Version, and VersionedAtTime
        situation_id = f"{attributes.get('SituationNumber', 'UNKNOWN')}_{attributes.get('Version', '0')}_{attributes.get('VersionedAtTime', '0000-00-00T00:00:00Z')}"
        print(f"Processing Situation: {situation_id}")


        # Check if the same situation already exists with the same data
        cursor.execute("""
            SELECT COUNT(*) FROM Situations 
            WHERE SituationID = ? 
        """, (situation_id,))
        exists = cursor.fetchone()[0]

        if exists > 0:
            print(f"Situation {situation_id} already exists. Skipping insertion.")
            continue

        # Insert into Situations table
        cursor.execute("""
            INSERT OR IGNORE INTO Situations (
                SituationID, SituationNumber, CreationTime, CountryRef, ParticipantRef, Version, Source_Type,
                Source_Name, VersionedAtTime, Progress, Validity_Start, Validity_End,
                Publication_Start, Publication_End, AlertCause, Priority, ScopeType, Language,
                Summary_DE, Summary_FR, Summary_IT, Summary_EN, Description_DE, Description_FR,
                Description_IT, Description_EN, Affects_StopPlace_Ref, Affects_StopPlace_Name,
                Affects_Facility_Ref, Affects_Facility_Name, Affects_Facility_Status,
                Conseq_Affects_StopPlace_Ref, Conseq_Affects_StopPlace_Name,
                Conseq_Affects_Facility_Ref, Conseq_Affects_Facility_Name,
                Conseq_Affects_Facility_Status, Publish_ScopeType, Publish_Affects_StopPlace_Ref,
                Publish_Affects_StopPlace_Name, PIA_ActionRef, PIA_RecordedAt, PIA_OwnerRef
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (situation_id,) + tuple(attributes.get(key) for key in [
            "SituationNumber", "CreationTime", "CountryRef", "ParticipantRef", "Version", "Source_Type",
            "Source_Name", "VersionedAtTime", "Progress", "Validity_Start", "Validity_End",
            "Publication_Start", "Publication_End", "AlertCause", "Priority", "ScopeType", "Language",
            "Summary_DE", "Summary_FR", "Summary_IT", "Summary_EN", "Description_DE", "Description_FR",
            "Description_IT", "Description_EN", "Affects_StopPlace_Ref", "Affects_StopPlace_Name",
            "Affects_Facility_Ref", "Affects_Facility_Name", "Affects_Facility_Status",
            "Conseq_Affects_StopPlace_Ref", "Conseq_Affects_StopPlace_Name",
            "Conseq_Affects_Facility_Ref", "Conseq_Affects_Facility_Name",
            "Conseq_Affects_Facility_Status", "Publish_ScopeType", "Publish_Affects_StopPlace_Ref",
            "Publish_Affects_StopPlace_Name", "PIA_ActionRef", "PIA_RecordedAt", "PIA_OwnerRef"
        ]))

        # Iterate through ALL PtSituationElement elements (situations)
        situations = root.findall(".//siri:PtSituationElement", namespace)
        # print(f"Found {len(situations)} situations in XML")  # Debugging output

        for situation in situations:
            situation_number = situation.findtext("siri:SituationNumber", default=None, namespaces=namespace)

            # **Filter out planned situations**
            planned_element = situation.find("siri:Planned", namespace)
            if planned_element is not None and planned_element.text.strip().lower() == "true":
                print(f"Skipping planned situation {situation_number}...")
                continue  # **Skip this situation if it is planned**

            # Extract situation details
            version = situation.findtext("siri:Version", default=None, namespaces=namespace)
            versioned_at_time = situation.findtext("siri:VersionedAtTime", default=None, namespaces=namespace)

            # Generate unique situation_id
            situation_id = f"{situation_number}_{version}_{versioned_at_time}"
            print(f"Processing Situation ID: {situation_id}")

            # Find all PassengerInformationAction elements inside this situation
            pia_actions = situation.findall(".//siri:PassengerInformationAction", namespace)
            # print(f"Found {len(pia_actions)} PassengerInformationAction elements for {situation_id}")

            
            # Extract Stop Point Affects
            for consequence in situation.findall(".//siri:Consequence", namespace):
                stop_points = consequence.findall(".//siri:AffectedStopPoint", namespace)

                for stop_point in stop_points:
                    
                    # Extract data for each stop point
                    stop_point_ref = stop_point.findtext("siri:StopPointRef", default=None, namespaces=namespace)
                    stop_point_name = stop_point.findtext("siri:StopPointName", default=None, namespaces=namespace)
                    longitude = stop_point.findtext("siri:Location/siri:Longitude", default=None, namespaces=namespace)
                    latitude = stop_point.findtext("siri:Location/siri:Latitude", default=None, namespaces=namespace)
                    stop_place_ref = stop_point.findtext("siri:StopPlaceRef", default=None, namespaces=namespace)
                    stop_place_name = stop_point.findtext("siri:StopPlaceName", default=None, namespaces=namespace)

                    # Extract accessibility information
                    mobility_access = stop_point.findtext("{http://www.siri.org.uk/siri}MobilityImpairedAccess", default=None, namespaces=namespace)
                    wheelchair_access = stop_point.findtext("{http://www.siri.org.uk/siri}WheelchairAccess", default=None, namespaces=namespace)
                    step_free_access = stop_point.findtext("{http://www.siri.org.uk/siri}StepFreeAccess", default=None, namespaces=namespace)
                    
                    # Check if the StopPoint already exists to prevent inserting duplicates for the same SituationID and StopPointRef
                    cursor.execute(""" 
                        SELECT COUNT(*) 
                        FROM StopPoints 
                        WHERE SituationID = ? AND StopPointRef = ?
                    """, (situation_id, stop_point_ref))
                    exists_stop_point = cursor.fetchone()[0]

                    if exists_stop_point == 0:
                        # Insert the stop point only if it doesn't already exist
                        cursor.execute(""" 
                            INSERT INTO StopPoints (
                                SituationID, StopPointRef, StopPointName, Longitude, Latitude, StopPlaceRef, StopPlaceName,
                                MobilityImpairedAccess, WheelchairAccess, StepFreeAccess
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (situation_id, stop_point_ref, stop_point_name, longitude, latitude, stop_place_ref, stop_place_name,
                            mobility_access, wheelchair_access, step_free_access))
                    else:
                        print(f"Skipping stop point entry for {situation_id}, StopPointRef {stop_point_ref} already exists.")


                
            for affected_network in situation.findall(".//siri:AffectedNetwork/siri:AffectedLine", namespace):
                operator_ref = affected_network.findtext("siri:AffectedOperator/siri:OperatorRef", default=None, namespaces=namespace)
                line_ref = affected_network.findtext("siri:LineRef", default=None, namespaces=namespace)
                published_line_name = affected_network.findtext("siri:PublishedLineName", default=None, namespaces=namespace)

                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM AffectedNetworks
                    WHERE SituationID = ? AND OperatorRef = ? AND LineRef = ?
                """, (situation_id, operator_ref, line_ref))
                exists_network = cursor.fetchone()[0]

                if exists_network == 0:
                    # If the record does not exist, insert the new record
                    cursor.execute("""
                        INSERT INTO AffectedNetworks (
                            SituationID, OperatorRef, LineRef, PublishedLineName
                        ) VALUES (?, ?, ?, ?)
                    """, (situation_id, operator_ref, line_ref, published_line_name))
                else:
                    print(f"Skipping network entry for {situation_id}, already exists.")

            for pia_action in pia_actions:
                # Find Perspective elements
                perspectives = pia_action.findall("siri:Perspective", namespace)

                for perspective in perspectives:
                    perspective_text = perspective.text.strip() if perspective.text else None
                    if perspective_text:
                        cursor.execute("SELECT COUNT(*) FROM Perspective WHERE SituationID = ? AND PIA_Perspective = ?", (situation_id, perspective_text))
                        exists_perspective = cursor.fetchone()[0]

                        if exists_perspective == 0:
                            # print(f"Inserting perspective {perspective_text} for {situation_id}")  # Debug
                            cursor.execute("""
                                INSERT INTO Perspective (
                                    SituationID, PIA_Perspective
                                ) VALUES (?, ?)
                            """, (situation_id, perspective_text))
                        else:
                            print(f"Skipping perspective {perspective_text} for {situation_id}, already exists")  # Debug

                # Iterate over all TextualContent elements within PassengerInformationAction
                textual_contents = pia_action.findall("siri:TextualContent", namespace)
                # print(f"{situation_id}: Found {len(textual_contents)} TextualContent elements")

                for textual_content in textual_contents:
                    # print(f"Checking SummaryContent for Situation {situation_id}: {'Found' if textual_content.find('siri:SummaryContent', namespace) is not None else 'Not Found'}")
                    # print(f"Checking ReasonContent for Situation {situation_id}: {'Found' if textual_content.find('siri:ReasonContent', namespace) is not None else 'Not Found'}")
                    # print(f"Checking DescriptionContent for Situation {situation_id}: {'Found' if textual_content.find('siri:DescriptionContent', namespace) is not None else 'Not Found'}")
                    # print(f"Checking RecommendationContent for Situation {situation_id}: {'Found' if textual_content.find('siri:RecommendationContent', namespace) is not None else 'Not Found'}")
                    # print(f"Checking DurationContent for Situation {situation_id}: {'Found' if textual_content.find('siri:DurationContent', namespace) is not None else 'Not Found'}")

                    text_size = textual_content.findtext("siri:TextualContentSize", default=None, namespaces=namespace)
                    text_size = text_size.strip() if text_size else None

                    text_size_map = {
                        "S": "Text_S",
                        "M": "Text_M",
                        "L": "Text_L"
                    }

                    if text_size in text_size_map:
                        table_name = text_size_map[text_size]

                        # Extract all language-specific texts
                        for section, xml_tag in {
                            "Summary": "SummaryContent",
                            "Reason": "ReasonContent",
                            "Description": "DescriptionContent",
                            "Recommendation": "RecommendationContent",
                            "Duration": "DurationContent",
                        }.items():
                            section_element = textual_content.find(f"siri:{xml_tag}", namespace)

                            if section_element is not None:
                                for text in section_element.findall("siri:*", namespace):
                                    lang = text.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "unknown").upper()
                                    value = text.text.strip() if text.text else None
                                    attributes[f"PIA_{section}_{lang}"] = value
                                    print(f"{situation_id} -> {xml_tag} ({lang}): {value}")
                                    
        
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE SituationID = ?", (situation_id,))
                        exists_text = cursor.fetchone()[0]

                        if exists_text == 0:
                            cursor.execute(f"""
                                INSERT INTO {table_name} (
                                    SituationID, PIA_Summary_DE, PIA_Summary_FR, PIA_Summary_IT, PIA_Summary_EN,
                                    PIA_Reason_DE, PIA_Reason_FR, PIA_Reason_IT, PIA_Reason_EN, PIA_Desc_DE, PIA_Desc_FR,
                                    PIA_Desc_IT, PIA_Desc_EN, PIA_Rec_DE, PIA_Rec_FR, PIA_Rec_IT, PIA_Rec_EN, PIA_Duration_DE,
                                    PIA_Duration_FR, PIA_Duration_IT, PIA_Duration_EN
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, tuple([situation_id] + [attributes.get(key) for key in [
                                "PIA_Summary_DE", "PIA_Summary_FR", "PIA_Summary_IT", "PIA_Summary_EN",
                                "PIA_Reason_DE", "PIA_Reason_FR", "PIA_Reason_IT", "PIA_Reason_EN",
                                "PIA_Description_DE", "PIA_Description_FR", "PIA_Description_IT", "PIA_Description_EN",
                                "PIA_Recommendation_DE", "PIA_Recommendation_FR", "PIA_Recommendation_IT", "PIA_Recommendation_EN",
                                "PIA_Duration_DE", "PIA_Duration_FR", "PIA_Duration_IT", "PIA_Duration_EN"
                                ]]))
                        else:
                            print(f"Skipping {situation_id}, already exists in {table_name}")  # Debug

            conn.commit()
    conn.close()

setup_database()
fetch_and_process_xml()
schedule.every().hour.do(fetch_and_process_xml)
#schedule.every().minute.do(fetch_and_process_xml)
while True:
    schedule.run_pending()
    time.sleep(60)
