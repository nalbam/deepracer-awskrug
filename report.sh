#!/bin/bash

OS_NAME="$(uname | awk '{print tolower($0)}')"

SHELL_DIR=$(dirname $0)

# URL_TEMPLATE="https://aws.amazon.com/api/dirs/items/search?item.directoryId=deepracer-leaderboard&sort_by=item.additionalFields.position&sort_order=asc&size=100&item.locale=en_US&tags.id=deepracer-leaderboard%23recordtype%23individual&tags.id=deepracer-leaderboard%23eventtype%23inperson&tags.id=deepracer-leaderboard%23eventid%23summit-season-2020-05-tt"
# URL_TEMPLATE="https://aws.amazon.com/api/dirs/items/search?item.directoryId=deepracer-leaderboard&sort_by=item.additionalFields.position&sort_order=asc&size=100&item.locale=en_US&tags.id=deepracer-leaderboard%23recordtype%23individual&tags.id=deepracer-leaderboard%23eventtype%23virtual&tags.id=deepracer-leaderboard%23eventid%23virtual-season-2020-05-tt"

URL_TEMPLATE1="https://aws.amazon.com/api/dirs/items/search?item.directoryId=deepracer-leaderboard&sort_by=item.additionalFields.position&sort_order=asc&size=100&item.locale=en_US&tags.id=deepracer-leaderboard%23recordtype%23individual&tags.id=deepracer-leaderboard%23eventtype%23"
URL_TEMPLATE2="&tags.id=deepracer-leaderboard%23eventid%23"

# SEASONS="2020-03-tt 2020-03-oa 2020-03-h2h"

# SEASON=$1

CHANGED=

# command -v tput > /dev/null && TPUT=true
TPUT=

_echo() {
    if [ "${TPUT}" != "" ] && [ "$2" != "" ]; then
        echo -e "$(tput setaf $2)$1$(tput sgr0)"
    else
        echo -e "$1"
    fi
}

_result() {
    _echo "# $@" 4
}

_command() {
    _echo "$ $@" 3
}

_success() {
    _echo "+ $@" 2
    exit 0
}

_error() {
    _echo "- $@" 1
    # exit 1
}

_prepare() {
    _command "_prepare"

    # rm -rf ${SHELL_DIR}/build

    mkdir -p ${SHELL_DIR}/build
    mkdir -p ${SHELL_DIR}/cache

    echo
}

_load() {
    TARGET=$1
    LEAGUE=$2
    SEASON=$3
    FILENAME=$4

    _command "_load ${LEAGUE} ${SEASON} ..."

    if [ -f ${SHELL_DIR}/cache/${FILENAME}.log ]; then
        cat ${SHELL_DIR}/cache/${FILENAME}.log > ${SHELL_DIR}/build/${FILENAME}.log
    fi

    URL="${URL_TEMPLATE1}${LEAGUE}${URL_TEMPLATE2}${SEASON}"

    curl -sL ${URL} \
        | jq -r '.items[].item | "\(.additionalFields.lapTime) \"\(.additionalFields.racerName)\" \(.additionalFields.points)"' \
        > ${SHELL_DIR}/cache/${FILENAME}.log

    _result "_load ${LEAGUE} ${SEASON} done"

    echo
}

_racer() {
    RACER=$1

    USERNAME=

    RACERS=${SHELL_DIR}/racers.json

    if [ -f ${RACERS} ]; then
        USERNAME="$(cat ${RACERS} | jq -r --arg RACER "${RACER}" '.[] | select(.racername==$RACER) | "\(.username)"')"

        if [ "${USERNAME}" != "" ]; then
            RACER="${RACER}   @${USERNAME}"
        fi
    fi

    RACER="${RACER}   :tada:"
}

_build() {
    TARGET=$1
    LEAGUE=$2
    SEASON=$3
    FILENAME=$4

    CHANGED=

    _command "_build ${LEAGUE} ${SEASON} ..."

    MESSAGE=${SHELL_DIR}/build/slack_message-${TARGET}.json

    MAX_IDX=20
    if [ "${TARGET}" == "h2h" ]; then
        MAX_IDX=32
    fi

    echo "{\"blocks\":[" > ${MESSAGE}
    echo "{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*AWS DeepRacer - ${SEASON}*\"}}," >> ${MESSAGE}

    IDX=1
    while read LINE; do
        if [ -f ${SHELL_DIR}/build/${FILENAME}.log ]; then
            COUNT=$(cat ${SHELL_DIR}/build/${FILENAME}.log | grep "${LINE}" | wc -l | xargs)
        else
            COUNT="0"
        fi

        ARR=(${LINE})

        NO=$(printf %02d $IDX)
        RECORD="${ARR[0]}"
        RACER=$(echo "${ARR[1]}" | sed -e 's/^"//' -e 's/"$//')

        if [ "x${COUNT}" == "x0" ]; then
            CHANGED=true

            if [ -f ${SHELL_DIR}/build/${FILENAME}.log ]; then
                RECORD="${RECORD}   ~$(cat ${SHELL_DIR}/build/${FILENAME}.log | grep "${ARR[1]}" | cut -d' ' -f1)~"
            fi

            _racer ${RACER}

            _result "changed ${RECORD} ${RACER}"
        fi

        TEXT="${NO}   ${RECORD}   ${RACER}"
        echo "{\"type\":\"context\",\"elements\":[{\"type\":\"mrkdwn\",\"text\":\"${TEXT}\"}]}," >> ${MESSAGE}

        if [ "${IDX}" == "${MAX_IDX}" ]; then
            break
        fi

        IDX=$(( ${IDX} + 1 ))
    done < ${SHELL_DIR}/cache/${FILENAME}.log

    echo "{\"type\":\"divider\"}" >> ${MESSAGE}
    echo "]}" >> ${MESSAGE}

    if [ "${CHANGED}" == "" ]; then
        rm -rf ${MESSAGE}
        _error "Not changed"
    fi

    # commit message
    printf "$(date +%Y%m%d-%H%M)" > ${SHELL_DIR}/build/commit_message.txt

    _result "_build ${LEAGUE} ${SEASON} done"

    echo
}

_run() {
    _prepare

    LIST=${SHELL_DIR}/build/league.txt

    cat ${SHELL_DIR}/league.json \
        | jq -r '.[] | "\(.target) \(.league) \(.season) \(.filename)"' \
        > ${LIST}

    while read LINE; do
        ARR=(${LINE})

        _load ${ARR[0]} ${ARR[1]} ${ARR[2]} ${ARR[3]}
        _build ${ARR[0]} ${ARR[1]} ${ARR[2]} ${ARR[3]}
    done < ${LIST}

    _success
}

_run
