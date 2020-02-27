import requests
import json
from conftest import print_timing
from fixtures import session
from conftest import saveRemoveDiagramCmd
import os
import pathlib
import pytest

#POST /rest/dependency-map/1.0/diagram
#POST /rest/dependency-map/1.0/linkConfig
#GET /plugins/servlet/dependency-map/diagram
#POST /rest/webResources/1.0/resources
#GET /rest/dependency-map/1.0/diagram?searchTerm=&startAt=0&maxResults=50
#POST /rest/webResources/1.0/resources

class TestChangeDiagram:
    @print_timing
    def test_change_diagram_config(self, session):
        HOSTNAME = os.environ.get('application_hostname')
        # Get user
        diagrams_response = session.get('http://'  + HOSTNAME + ':8080/rest/dependency-map/1.0/user')
        assert diagrams_response.status_code == 200
        userKey = diagrams_response.json()["key"]
        print("User key: " + userKey)

        # Create diagram
        payload ={ 'name':"D100", 'author':userKey,
           'lastEditedBy':userKey, 'layoutId':0, 'filterKey': 10000,
            'boxColorFieldKey': "priority", 'groupedLayoutFieldKey': "priority", 
            'matrixLayoutHorizontalFieldKey': 'fixVersions', 'matrixLayoutVerticalFieldKey': 'fixVersions'}

        diagrams_response = session.post('http://' + HOSTNAME + ':8080/rest/dependency-map/1.0/diagram',
            json=payload)
        assert diagrams_response.status_code == 200    
        newDiagram = diagrams_response.json()
        diagramId = str(newDiagram["id"])
        print('diagramid=' +diagramId)

        saveRemoveDiagramCmd(diagramId)
         
        # Get all priorities
        diagrams_response = session.get('http://' + HOSTNAME + ':8080/rest/dependency-map/1.0/fieldOption/priority')
        assert diagrams_response.status_code == 200            
        priorityItem = diagrams_response.json()[4]
        priorityItemId = str(priorityItem['id'])
        print('priorityItemId=' + priorityItemId)
        
        #Get colore palete entry for diagram for field=priority option=5 
        diagrams_response = session.get('http://' + HOSTNAME + ':8080/rest/dependency-map/1.0/boxColor?diagramId=' + diagramId + '&fieldId=priority&fieldOptionId=' + priorityItemId)
        assert diagrams_response.status_code == 200            
        value = diagrams_response.text
        if not value:
           print( "No response value")
        else:
           print( diagrams_response.json() ) 

        #create box coloure resource entry
        payload = {"diagramId":diagramId,"fieldId":"priority","fieldOptionId":priorityItemId,"colorPaletteEntryId":4}
        diagrams_response = session.post('http://' + HOSTNAME + ':8080/rest/dependency-map/1.0/boxColor',
            json=payload)
        assert diagrams_response.status_code == 200
        print( diagrams_response.json() )
        boxColorResource = diagrams_response.json()['id']
        
        #update box coloure resource entry, created if not exists.
        payload = {"id":boxColorResource,"diagramId":diagramId,"fieldId":"priority","fieldOptionId":priorityItemId,"colorPaletteEntryId":5}
        diagrams_response = session.put('http://' + HOSTNAME + ':8080/rest/dependency-map/1.0/boxColor',
            json=payload)
        assert diagrams_response.status_code == 200
        print( diagrams_response.json() )
        
        
    
           
        
        
              
        
 
