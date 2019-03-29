google.load("visualization", "1", {packages:["corechart"], 'language': 'en'});

(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users_data", function(result) {
            result.sort(function(a, b) {
                return (a.name).localeCompare((b.name));
            });
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name).attr('avatar', this.avatar))
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
                $.getJSON("/api/v1/presence_weekday/"+selected_user, function(result) {
                    var data = google.visualization.arrayToDataTable(result);
                    var options = {};
                    chart_div.show();
                    user_img.show();
                    loading.hide();
                    var chart = new google.visualization.PieChart(chart_div[0]);
                    chart.draw(data, options);
                });
            }
            else{
                user_img.hide();
                chart_div.hide();
            }
        });
    });
})(jQuery);
