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
            var no_data = $('#no_data');
            if(selected_user) {
                var avatar = $('option:selected').attr('avatar');
                user_img.attr("src", avatar);
                user_img.show();
                loading.show();
                chart_div.hide();
                no_data.hide();
                $.getJSON("/api/v1/presence_weekday/"+selected_user, function(result) {
                    var data = google.visualization.arrayToDataTable(result);
                    var options = {};
                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.PieChart(chart_div[0]);
                    chart.draw(data, options);
                })
                    .fail(function (api_response) {
                        if(api_response.status === 404){
                            loading.hide();
                            no_data.show();
                        }
                    })
            }
            else{
                user_img.hide();
                chart_div.hide();
                no_data.hide();
            }
        });
    });
})(jQuery);
