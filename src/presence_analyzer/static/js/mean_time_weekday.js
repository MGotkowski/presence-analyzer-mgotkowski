google.load("visualization", "1", {packages:["corechart"], 'language': 'pl'});

(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users_data", function(result) {
            result.sort(function(a, b) {
                return (a.name).localeCompare((b.name));
            });
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
            var user_img = $('#user_img');
            if(selected_user) {
                var avatar = $('option:selected').attr('avatar');
                user_img.attr("src", avatar);
                loading.show();
                chart_div.hide();
                $.getJSON("/api/v1/mean_time_weekday/"+selected_user, function(result) {
                    $.each(result, function(index, value) {
                        value[1] = parseInterval(value[1]);
                    });
                    var data = new google.visualization.DataTable();
                    data.addColumn('string', 'Weekday');
                    data.addColumn('datetime', 'Mean time (h:m:s)');
                    data.addRows(result);
                    var options = {
                        hAxis: {title: 'Weekday'}
                    };
                    var formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'});
                    formatter.format(data, 1);

                    user_img.show();
                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.ColumnChart(chart_div[0]);
                    chart.draw(data, options);
                });
            }
            else {
                user_img.hide();
                chart_div.hide();
            }
        });
    });
})(jQuery);
