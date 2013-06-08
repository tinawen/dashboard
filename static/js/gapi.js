var map;
function locate() {
    var mapOptions = {
        disableDefaultUI: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

    $.getJSON($SCRIPT_ROOT + '/location', {
    }, function(data) {
        var tina_pos = new google.maps.LatLng(data.tina.latitude, data.tina.longitude);
        map.setCenter(tina_pos);
        var eric_pos = new google.maps.LatLng(data.eric.latitude, data.eric.longitude);
        new google.maps.Marker({position: eric_pos, icon: '/static/img/eric.png', map: map});
        new google.maps.Marker({position: tina_pos, icon: '/static/img/tina.png', map: map});
        var latlngbounds = new google.maps.LatLngBounds();
        latlngbounds.extend(tina_pos);
        latlngbounds.extend(eric_pos);
        map.fitBounds(latlngbounds);
    });
}

function get_events() {
    $.getJSON($SCRIPT_ROOT + '/calendar', {
    }, function(events) {
        $('#events').empty()
        events.forEach( function(e) {
            $('#events').append(
                $('<li>').append(
                    $('<span>').text(e.date).addClass('date'))
                    .append(
                        $('<span>').text(e.time).addClass('time'))
                    .append(
                        $('<span>').text(e.summary).addClass('summary')).addClass(e.label)
            )
        });
    });
}

function get_tasks() {
    $.getJSON($SCRIPT_ROOT + '/tasks', {
    }, function(tasks) {
        $('#tasks').empty()
        tasks.forEach( function(t) {
            inner = $('<li>').append($('<span>').text(t.title).addClass('title'))
            if (t.due)
                inner.append($('<span>').text(t.due).addClass('due'))
            $('#tasks').append(inner.addClass(t.label))
        });
    });
}

function take_picture() {
    $.getJSON($SCRIPT_ROOT + '/picture', {
    }, function(file_name) {
        $('#webcam img').attr('src', file_name);
    });
}

function reload() {
    locate();
    get_events();
    get_tasks();
    take_picture();
    console.log("reloading...");
    // refresh every 5 mins
    setTimeout(function(){reload()}, 300000);
}

google.maps.event.addDomListener(window, 'load', reload);
