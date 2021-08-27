#!/bin/bash

start=$(date +%s)

BAMBOO_URL="http://3.133.150.205:8085"
USERNAME="admin"
PASSWORD="admin"
REMOTE_AGENTS_COUNT=10

AGENT_JAR_URL=$BAMBOO_URL/agentServer/agentInstaller
AGENT_JAR=agentInstaller.jar
AGENT_HOME="bamboo-agent-home"

echo NUMBERS OF REMOTE AGENTS: $REMOTE_AGENTS_COUNT
echo BAMBOO INSTANCE URL: $BAMBOO_URL
echo BAMBOO CREDENTIALS: $USERNAME/$PASSWORD
echo  # move to a new line

echo "Step1: Check Java"
if ! [[ -x "$(command -v java)" ]]; then
  echo "Install openjdk with apt-get"
  sudo apt-get update && sudo apt-get install -y openjdk-11-jre-headless
  if [[ $? -ne 0 ]]; then
    echo "Java was NOT installed. Please install Java manually."
    exit 1
  fi
fi
echo "Java version:"
java -version
echo  # move to a new line


echo "Step2: Cleanup"
echo "Stop existing agents processes"
pkill -f "agentServer"

echo "Clean up previous agents files"
rm -rf $AGENT_HOME* $AGENT_JAR
echo  # move to a new line


echo "Step3: Download agent installer"
curl $AGENT_JAR_URL --output $AGENT_JAR
echo  # move to a new line


echo "Step4: Start agents"
# start agents
for ((i=1;i<=REMOTE_AGENTS_COUNT;i++))
do
  java -jar -Dbamboo.home=$AGENT_HOME"$i" -Dbamboo.fs.timestamp.precision=1000000 $AGENT_JAR $BAMBOO_URL/agentServer/ > /dev/null 2>&1 &
  echo Agent "$i/$REMOTE_AGENTS_COUNT" started
done
echo  # move to a new line


echo "Step5: Authenticate agents"
# authenticate created agents
for ((i=1;i<=REMOTE_AGENTS_COUNT;i++))
do
  attempts=100
  sleep_time=5

  retries=0
  while [ ! -f "$HOME/$AGENT_HOME$i/uuid-temp.properties" ]
  do
    ((retries+=1))
    if [ "$retries" -eq "$attempts" ]; then
      echo "Terminated due to timeout. Agent $i uuid-temp.properties file not found in $attempts attempts."
      exit 1
    fi
    echo "Waiting for agent $i/$REMOTE_AGENTS_COUNT temp properties file creation. Attempt $retries/$attempts. Sleeping $sleep_time seconds."
    sleep $sleep_time
  done

  echo "Starting authentication of agent $i/$REMOTE_AGENTS_COUNT"
  attempts=100
  sleep_time=5
  retries=0

  auth_response=-1
  while [ "$retries" -lt "$attempts" ] && [ "$auth_response" != "0" ]
  do
      ((retries+=1))
      properties=$(sed -n -e 's/.*agentUuid\=//p' "$HOME/$AGENT_HOME$i/uuid-temp.properties")
      curl -s --fail --show-error -X PUT --user $USERNAME:$PASSWORD "$BAMBOO_URL/rest/api/latest/agent/authentication/$properties"
      auth_response=$?
      echo "Auth response for agent $i/$REMOTE_AGENTS_COUNT: $auth_response"
      if [ "$auth_response" != "0" ]; then
        echo "Waiting for agent $i/$REMOTE_AGENTS_COUNT authentication. Attempt $retries/$attempts. Sleeping $sleep_time seconds."
        sleep $sleep_time
      fi
  done
  if [ "$auth_response" != "0" ]; then
    echo "Unable to authenticate agent $i in $attempts attempts"
    exit 1
  fi
  echo "Agent $i/$REMOTE_AGENTS_COUNT has been authenticated"

done
echo  # move to a new line


echo "Step6: Wait for agents to be ready"
for ((i=1;i<=REMOTE_AGENTS_COUNT;i++))
do
  attempts=200
  sleep_time=5
  retries=0
  check_grep=""

  while [ -z "$check_grep" ]
  do
    ((retries+=1))
    check_grep=$(grep "ready to receive builds" "$HOME/$AGENT_HOME$i/atlassian-bamboo-agent.log")
    if [ "$retries" -eq "$attempts" ]; then
      echo "Terminated due to timeout. Agent $i is not ready in $attempts attempts."
      exit 1
    fi
    if [ -z "$check_grep" ]; then
      echo "Waiting for agent $i/$REMOTE_AGENTS_COUNT to be ready. Attempt $retries/$attempts. Sleeping $sleep_time seconds."
      sleep $sleep_time
    fi
  done
  echo "Agent $i/$REMOTE_AGENTS_COUNT ready to receive builds"
done
echo  # move to a new line

end=$(date +%s)
echo "DCAPT util script execution is finished successfully in $((end-start)) seconds."