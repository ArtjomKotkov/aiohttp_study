export {user_info};

var user_info = Vue.component('user_info', {
        props:['user', 'owner'],
        template: `
            <div class='flex-grow-1 d-flex flex-row justify-content-center align-items-center pb-3'>
                <div class='w-100 d-flex flex-shrink-1 flex-row justify-content-center align-items-center'>
                    <div class='width-third'>
                        <div class='d-flex justify-content-end p-3'>
                            {{description}}
                        </div>
                    </div>
                    <div style='width-third width: 150px; height: 150px; border-radius: 50%;' class='overflow-hidden'>
                        <img :src="user_img" alt="" width='150px' height='150px'/>
                    </div>
                    <div class='width-third d-flex flex-row justify-content-start align-items-left p-3'>
                        <div class='d-flex flex-column justify-content-start align-items-center'>
                            <p class='mb-2 d-block'>Подписчики: {{subscribers}}</p>
                            <a href='#' class='subscribe' v-if='!subscribed && subscribed != null'>Подписаться</a>
                            <a href='#' class='unsubscribe' v-if='subscribed && subscribed != null'>Отписаться</a>
                        </div>
                    </div>
                </div>
            </div>
        `,
        data: function () {
            return {
                subscribers: 0,
                subscribed: null
            }
        },
        mounted () {
            axios.get(`/user/subscriber/?mode=subscribers&user=${this.owner.name}&limit=0`, {
            }).then((response) => {
              this.subscribers = response.data.count
            });
            if (this.user.name == this.owner.name) {
                return this.subscribed = null
            } else {
                axios.get(`/user/subscriber/?mode=check&owner=${this.owner.name}&user=${this.user.name}`, {
                }).then((response) => {
                    return this.subscribed = response.data.status
                });
            }
        },
        computed: {
            user_img () {
                return this.user.photo != null ? this.user.photo : '/static/img/no-user-photo.png'
            },
            description () {
                return this.user.description != null ? this.user.description : ''
            }
        }
    })