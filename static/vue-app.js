$(document).ready(function () {

    var app = new Vue({
        el: '#app',
        data: {
            message: 'Test',
            info: null
        },
        mounted() {
            axios({
                method: 'get',
                url: '/content/art',
                data: {
					limit: 1000
                },
				contentType: 'application/json'
            })
                .then(response => (this.info = response))
        },
        delimiters: ['[[', ']]']
    })

});