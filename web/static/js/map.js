var coords = [42.878593, -8.519403];
var map = L.map('map').setView(coords, 14);

var provider = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
    subdomains: 'abcd',
    maxZoom: 17
});

map.addLayer(provider);

var LeafIcon = L.Icon.extend({
    options: {
        //iconSize:       [36, 36],
        iconAnchor: [18, 18]
    }
});

var neutralIcon = new LeafIcon({iconUrl: 'static/gyms/Uncontested.png'});
var mysticIcon = new LeafIcon({iconUrl: 'static/gyms/Mystic.png'});
var valorIcon = new LeafIcon({iconUrl: 'static/gyms/Valor.png'});
var instinctIcon = new LeafIcon({iconUrl: 'static/gyms/Instinct.png'});


var gymsData = {};
var markers = {};
var lastUpdated = 0;
var firstLoad = true;

var id = 0;

function updateMap() {
    var url = lastUpdated > 0 ? 'gyms?after=' + lastUpdated : 'gyms';

    $.getJSON(url, function (data) {
        lastUpdated = data.timestamp;
        var gyms = data.gyms;
        var text = data.timestamp + ": " + gyms.length + " gyms";
        console.log(text);
        var date = moment.unix(lastUpdated);
        $("#updated_at").text(date.add(2, 'hours').format("HH:mm, DD/MM/YYYY"));
        for (var i in gyms) {
            var gym = gyms[i];

            // console.log(gym);
            var team = parseInt(gym.team_id);
            var icon = neutralIcon;
            switch (team) {
                case 1:
                    icon = mysticIcon;
                    break;
                case 2:
                    icon = valorIcon;
                    break;
                case 3:
                    icon = instinctIcon;
            }

            var popupText = `<h3> ${gym.name}</h3>
            <img src=${icon.options.iconUrl}>
            <ul>
            <li>nivel ${gym.level}</li>
            <li>${gym.gym_points} puntos</li>
            <li>${gym.members_count} entrenadores</li>
            </ul>
            `;

            if (gym.id in markers) {
                markers[gym.id].setIcon(icon);
                markers[gym.id].getPopup().setContent(popupText);

            } else {
                markers[gym.id] = L.marker([gym.latitude, gym.longitude], {icon: icon})
                    .addTo(map).bindPopup(popupText);
            }
        }

        gymsDiff(gyms);

        for (var i in gyms) {
            gymsData[gyms[i].id] = gyms[i];
        }
        updateStats();
    });
}

function getTeamSpan(team_id) {
    switch (team_id) {
        case 0:
            return `<span class="highlight">Neutral</span>`;
        case 1:
            return `<span class="highlight t1">Mystic</span>`;
        case 2:
            return `<span class="highlight t2">Valor</span>`;
        case 3:
            return `<span class="highlight t3">Instinct</span>`;
    }
}

function gymsDiff(gyms) {
    if (!firstLoad) {


        for (var i in gyms) {
            gym = gyms[i];

            var date = moment.unix(lastUpdated);

            var oldGym = gymsData[gym.id];

            var oldTeamSpan = getTeamSpan(oldGym.team_id);
            var newTeamSpan = getTeamSpan(gym.team_id);
            var gymNameHighlight = `<span class="highlight">${gym.name}</span>`;

            var text;
            var popup;
            if (gym.team_id != oldGym.team_id) {
                if (gym.team_id != 0) {
                    if (oldGym.team_id == 0) {
                        text = `${newTeamSpan} ahora controla ${gymNameHighlight}`;
                    } else {
                        text = `${newTeamSpan} ha conquistado ${gymNameHighlight} a ${oldTeamSpan}`;
                    }
                    popup = "Conquistado!";
                } else {
                    popup = "Derrotado!";
                    text = `${oldTeamSpan} ha sido derrotado en ${gymNameHighlight}`;
                }
            } else {
                var diff_points = gym.gym_points - oldGym.gym_points;
                console.log(diff_points +" " + gym.members_count + " " + oldGym.members_count);
                if( diff_points == 2000 && (gym.members_count - oldGym.members_count) == 1){
                    text = `${newTeamSpan} ha añadido un entrenador a ${gymNameHighlight} (+${diff_points})`;
                    popup = "+" + diff_points;
                }else if (diff_points > 0) {
                    text = `${newTeamSpan} ha entrenado ${gymNameHighlight} (+${diff_points})`;
                    popup = "+" + diff_points;
                } else if (diff_points < 0) {
                    text = `${newTeamSpan} está siendo atacado en ${gymNameHighlight} (${diff_points})`;
                    popup = diff_points;
                }
            }

            if (text) {
                $("#changes").prepend(`<li><small>${date.add(2, 'hours').format("HH:mm:ss")}</small> ${text}<br></li>`);
            }

            if (popup) {
                var point = map.latLngToContainerPoint([gym.latitude, gym.longitude]);
                $("<div>", {
                    id: `popup_${id}`,
                    text: popup,
                    class: "popup",
                    css: {
                        top: point.y,
                        left: point.x
                    }
                }).appendTo('#map_wrapper').fadeIn(1000, function () {
                    $(this).fadeOut({
                        duration: 5000,
                        queue: false,
                        complete: function () {
                            $(this).remove();
                        }
                    });
                    $(this).animate({top: "-=50px"}, 'slow');
                });
            }
        }

        id++;
    }
    firstLoad = false;
}


function updateStats() {
    var team_count = {
        'neutral': 0,
        'mystic': 0,
        'valor': 0,
        'instinct': 0
    };

    for (var id in gymsData) {
        switch (gymsData[id].team_id) {
            case 0:
                team_count['neutral']++;
                break;
            case 1:
                team_count['mystic']++;
                break;
            case 2:
                team_count['valor']++;
                break;
            case 3:
                team_count['instinct']++;
                break;
        }
    }

    for (team in team_count) {
        if (team == 0) {
            continue;
        }
        var percentage = team_count[team] / Object.keys(gymsData).length * 100;
        $('#' + team + '_count').text(`${team_count[team]} gyms (${percentage.toFixed(2)} %)`);
    }
}

$(function () {
    updateMap();
    window.setInterval(updateMap, 5000);
});


