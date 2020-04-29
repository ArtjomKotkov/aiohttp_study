$(document).ready(function () {

    var app = new Vue({
        el: '#app',
        data: {
            raw: null,
            info: null,
            art_width: 250,
            window_width: null,
            window_height: null,
        },
        mounted() {
            this.window_width = window.innerWidth
            this.window_height = window.innerHeight 
            axios({
                method: 'get',
                url: '/content/art',
				contentType: 'application/json'
            })
            .then(function (response) {
                app.raw = response.data.items.slice();
                var newObject = Object.assign({}, response.data.items)
                console.log(newObject)
                app.info = create_array(app.raw, app.arts_in_line, app.art_width)
            });
            window.addEventListener('resize', () => {
                if (app.raw !== null){
                    this.window_width = window.innerWidth
                    this.window_height = window.innerHeight 
                    app.info = create_array(this.raw, this.arts_in_line, this.art_width)
                }
            });
        },
        delimiters: ['[[', ']]'],
        computed: {
            arts_in_line () {0
                var value = parseInt((this.window_width - 24*2) / (this.art_width+10));
                if (value < 1) {
                    value = 1;
                }
                return value;
            },
            center_div_width ()  {
                return this.arts_in_line * (this.art_width + 10)
            }
        }
    })
    Vue.component('photo', {
        props: ['item', 'art_width'],
        template: `<a class='art' href="" :style="offset(item.offsetX, item.offsetY)" @mouseover="hover = true" @mouseout="hover = false">
                       <img v-bind:src="/media/ + item.path" class="img" :width="art_width+'px'">
                       <a href="" class='download-art' v-show='hover'>Скачать</a>
                   </a>`,
        data: function () {
            return {
                hover: false,
            }
        },
        updated () {
            console.log(this.hover)
        },
        methods: {
            offset (valueX, valueY) {
              return `transform: translateX(${ valueX }) translateY(${ valueY })`
            }
        },
    })

});


function create_array(info, arts_in_line, art_width) {
    var multi_array = [];
    // Create mulri array
    for (var index = 0; index < info.length; index = index + arts_in_line) {
        multi_array.push(info.slice(index, index+arts_in_line));
    }
    // Save vertical offsets
    var top_offset = []
    for (var row = 0; row < multi_array.length; row ++) {
        for (var col = 0; col < multi_array[row].length; col ++) {
            // scale of art
            let scale = art_width / multi_array[row][col]['width'];
            // Calculation new height and offsetX/Y values
            if (row == 0) {
                top_offset[col] = parseInt(multi_array[row][col]['height'] * scale) + 10;
                multi_array[row][col]['offsetY'] = 0;
                multi_array[row][col]['offsetX'] = (art_width+10) * col + 'px';
            } 
            else {
                multi_array[row][col]['offsetY'] = top_offset[col] + 'px';
                top_offset[col] = top_offset[col] + parseInt(multi_array[row][col]['height']) * scale + 10;
                multi_array[row][col]['offsetX'] = (art_width+10) * col + 'px';
            }
        }
    }
    return multi_array;
}