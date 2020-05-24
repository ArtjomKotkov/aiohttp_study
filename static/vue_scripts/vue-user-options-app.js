
$(document).ready(function () {

	Vue.component('common_options', {
		props: ['user'],
	    template: `
	    	<div class='p-3'>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div>Имя пользователя</div>
						<p>Тут имя</p>
						<a href="#" class='d-block' v-if='selected != 1' @click.prevent='selected = 1'>Изменить</a>
						<a href="#" class='d-block' v-if='selected == 1' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div v-if='selected == 1' class='d-flex flex-row justify-content-start align-items-top'>
						<div>
							<span>Новое имя пользователя</span>
						</div>
						<div>
							<input type="text" />
							<a href="#" @click.prevent class='default-button button_focus'>Изменить</a>
						</div>
						
					</div>
	    		</div>
	    		<hr>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div>Пароль</div>
						<p>Тут пароль</p>
						<a href="#" class='d-block' v-if='selected != 2' @click.prevent='selected = 2'>Изменить</a>
						<a href="#" class='d-block' v-if='selected == 2' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div></div>
	    		</div>
	    		<hr>
	    	</div>
	    `,
	    data: function () {
	        return {
	        	selected: null
	        }
	    },
	    computed: {
	    }
	})

	var app = new Vue({
	    el: '#app',
	    data: {
	    },
	    delimiters: ['[[', ']]'],
	})

	Vue.component('user_options', {
		props: ['user'],
	    template: `
	    <div id='user_options' class='d-flex flex-row shadow'>
		    <div class='h-100' id='user_options_left_menu'>
		    	<div class=''>
		    		<img :src="user_img" alt="" id='user_options_left_menu_img'/>
		    	</div>
		    	<div class='user_options_left_menu_description'>
		    		<p text-align='center'>{{description}}</p>
		    	</div>
		    	<div class='d-flex flex-column justify-content-start align-items-left'>
					<div v-bind:class="{ option_menu_item_selected: selected == 1 }" class='change_cursor_pointer option_menu_item' @click.prevent='selected = 1'>Общее</div>
					<div v-bind:class="{ option_menu_item_selected: selected == 2 }" class='change_cursor_pointer option_menu_item' @click.prevent='selected = 2'>Безопасность</div>
		    	</div>
		    </div>
			<div class='h-100 w-100'>
				<common_options v-if='selected == 1'></common_options>
		    </div>
	    </div>
	    `,
	    data: function () {
	        return {
	        	selected: 1
	        }
	    },
	    computed: {
	    	description () {
	    		return this.user.description === undefined ? 'Без описания' : this.user.description
	    	},
            user_img () {
                return this.user.photo != null ? this.user.photo : '/static/img/no-user-photo.png'
            },
	    }
	})

	var app = new Vue({
	    el: '#app',
	    data: {
	    },
	    delimiters: ['[[', ']]'],
	})

})