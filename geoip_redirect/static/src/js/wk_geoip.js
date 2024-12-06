/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('geoip_redirect.wk_geoip', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function () {
        var val = $('.blockedcountry').val();
        if (val) {
            $.blockUI({
                message: $('.wk_blocked_page'),
                css: {
                    border: 'none',
                    width: 'auto',
                    top: 0,
                    right: 0,
                    left: 0,
                    padding: '15px',
                    backgroundColor: '#da5c5f',
                    opacity: .9,
                },
            });
        } else {
            getLocation();
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(showPosition);
                } else {
                    $.getJSON('//api.ipify.org/?format=json/', function(data){
                        console.log(data);
                        ajax.jsonRpc("/redirect/location", 'call', { 'ip': data.ip })
                            .then(function (data_1) {
                                if (data_1) {
                                    var path = window.location.pathname;
                                    if (path.includes(data_1[1])) {
                                        path = path.replace(data_1[1], data_1[0]);
                                    } else {
                                        path = "/" + data_1[0] + path;
                                    }
                                    var redirect = {
                                        lang: data_1[0],
                                        url: encodeURIComponent(path.replace(/[&?]edit_translations[^&?]+/, '')),
                                        hash: encodeURIComponent(window.location.hash)
                                    };
        
                                    if (data_1[2]) {
                                        window.location.href = data_1[2];
                                    } else {
                                        window.location.href = _.str.sprintf("/website/lang/%(lang)s?r=%(url)s%(hash)s", redirect);
                                    }
        
                                }
                            })
        
                    });
                }
            }

            function showPosition(position) {
                console.log("position");
                console.log(position);
                let mapurl = "//nominatim.openstreetmap.org/reverse?lat=" + position.coords.latitude + "&lon="+ position.coords.longitude+ "&zoom=10&format=json"
                console.log(mapurl);
                $.getJSON(mapurl, function(data){
                    console.log(data);
                    let country_code = data.address.country_code
                    let country = data.address.country
                    ajax.jsonRpc("/redirect/location", 'call', { 'country_code': country_code, 'country_name':country})
                        .then(function (data_1) {
                            if (data_1) {
                                var path = window.location.pathname;
                                if (path.includes(data_1[1])) {
                                    path = path.replace(data_1[1], data_1[0]);
                                } else {
                                    path = "/" + data_1[0] + path;
                                }
                                var redirect = {
                                    lang: data_1[0],
                                    url: encodeURIComponent(path.replace(/[&?]edit_translations[^&?]+/, '')),
                                    hash: encodeURIComponent(window.location.hash)
                                };

                                if (data_1[2]) {
                                    window.location.href = data_1[2];
                                } else {
                                    window.location.href = _.str.sprintf("/website/lang/%(lang)s?r=%(url)s%(hash)s", redirect);
                                }

                            }
                        })
                });
            }
        }
        $(".dropdown-content").hover(function () {
            $('#geoCountryList').show();
        },
            function () {
                $('#geoCountryList').hide();
            });

        $('.wkselectedCountry').on('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var countryId = $(this).attr('data-country');
            var lang = $(this).attr('data-lang');
            var href = $(this).attr('shref');
            if (!href.includes(lang)) {
                var redirect = {
                    lang: lang,
                    url: href
                };
                href = _.str.sprintf("/website/lang/%(lang)s?r=%(url)s", redirect);
            }

            ajax.jsonRpc("/change/country", 'call', { 'countryId': countryId, 'lang': lang })
                .then(function (data) {
                    window.location.href = href;
                })

        });
    });

})
