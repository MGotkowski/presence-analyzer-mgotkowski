google.load("visualization", "1", {packages:["calendar"], 'language': 'en'});

function getDate(value) {
    return new Date(value)
}

(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users_data", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name).attr('avatar', this.avatar));
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function(){
            var selected_user = $("#user_id").val();
            var chart_div = $('#chart_div');
            if(selected_user) {
                var avatar = $('option:selected').attr('avatar');
                $('#user_img').attr("src", avatar);
                loading.show();
                chart_div.hide();
                $.getJSON("/api/v1/presence_days/"+selected_user, function(result) {
                    $.each(result, function(index, value) {
                        value[0] = getDate(value[0]);
                    });
                    var data = new google.visualization.DataTable();
                    data.addColumn({ type: 'date', id: 'Date' });
                    data.addColumn({ type: 'number', id: 'Presence time'});
                    data.addRows(result);

                    var options = {
                        calendar: { cellSize: 13 }
                    };

                    var date_formatter = new google.visualization.DateFormat({pattern: 'dd-MM-yyyy'});
                    date_formatter.format(data, 0);

                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.Calendar(chart_div[0]);
                    chart.draw(data, options);
                });
            }
        });
    });
})(jQuery);
