$(document).ready(function () {

    Vue.directive('click-outside', {
      bind: function (el, binding, vnode) {
        this.event = function (event) {
          if (!(el == event.target || el.contains(event.target))) {
            vnode.context[binding.expression](event);
          }
        };
        document.body.addEventListener('click', this.event)
      },
      unbind: function (el) {
        document.body.removeEventListener('click', this.event)
      },
    });

    component = Vue.component('cmenu_component', {
        props: ['name'],
        template: `<div class='context-menu-item'>
                       <a href="#" class='context-menu-item-text' @click='click(name)'><slot></slot></a>
                   </div>`,
        data: function () {
            return {
            }
        },
        methods: {
            click () {
                switch(this.name) {
                    case "Download":
                        console.log('Download')
                        break;
                    case "Share":
                        console.log('Share')
                        break;
                }
            }
        }  
    })


    menu = Vue.component('cmenu', {
        template: `<div class='context-menu shadow' :style='style' v-if='opened' v-click-outside="close">
                       <div class='m-1'><span class='m-auto context-menu-header d-block text-center'><slot name="header"></slot></span></div>
                       <hr class='m-0'>
                       <div><slot></slot></div>
                   </div>`,
        data: function () {
            return {
                opened: false,
                style: { 
                    left: 0,
                    top: 0,
                    'z-index': '4'
                },
                item: null,
                menu_button: null,
                height: 200,
                width: 300
            }
        },
        methods: {
            open: function (ev, menu_button, item) {
                if (this.opened == true) {
                    this.item = null;
                    this.opened = false;
                    this.menu_button = null;
                }
                this.item = item;
                this.opened = true;
                this.menu_button = menu_button;
                if (window.innerWidth < ev.clientX + this.width) {
                    this.style = { 
                        left: ev.clientX-this.width-30+'px',
                        top: (ev.clientY-this.height/2)+'px',
                        'z-index': '4',
                        width: this.width+'px',
                        height: this.height+'px',
                    }
                } else {
                    this.style = { 
                        left: ev.clientX+30+'px',
                        top: (ev.clientY-this.height/2)+'px',
                        'z-index': '4',
                        width: this.width+'px',
                        height: this.height+'px',
                    }
                }
            },
            close (event) {
                if(Object.is(event.target, this.menu_button) == false) {
                    this.item = null;
                    this.opened = false;
                    this.menu_button =null;
                }
            }
        },
        components: {
            "cmenu-component":component
        }
    })


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
        },
    })
    
    Vue.component('photo', {
        props: ['item', 'art_width', 'menu'],
        template: `<span class='art' :style="offset(item.offsetX, item.offsetY)" @mouseover="hover = true" @mouseout="hover = false">
                        <img v-bind:src="/media/ + item.path" class="img" :width="art_width+'px'" @click='enter_art'>
                        <a href="#" class='art-owner' align="center" v-show='hover'>{{item.owner}}</a>
                        <a href="#" class='art-menu' align="center" v-show='hover' ref='menu_button' @click.prevent='menu.open($event, $refs.menu_button, item)'>...</a>
                   </span>`,
        data: function () {
            return {
                hover: false,
            }
        },
        methods: {
            offset (valueX, valueY) {
              return `transform: translateX(${ valueX }) translateY(${ valueY })`
            },
            enter_art () {
                document.location.href = `/user/${this.item.owner}/art/${this.item.id}`;
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