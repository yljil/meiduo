var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'], // 修改vue模板符号，防止与django冲突
    data: {
        host,
        f1_tab: 1, // 1F 标签页控制
        f2_tab: 1, // 2F 标签页控制
        f3_tab: 1, // 3F 标签页控制
        cart_total_count: 0, // 购物车总数量
        carts: [], // 购物车数据,
        username:'',
        content_category:[],
        showCart: false,
        debounceTimer: null
    },
    mounted(){
        // 获取购物车数据
        // this.get_carts();

         // 获取cookie中的用户名
    	this.username = this.getCookie('username');  // 改为 this.getCookie


        this.get_cart()
    },
    methods: {
        // 添加 getCookie 方法
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        // get_category_data:function(){
        //     var url = this.host + '/content_category/';
        //     axios.get(url, {
        //         responseType: 'json',
        //     })
        //         .then(response => {
        //             this.content_category = response.data.content_category
        //         })
        //         .catch(error => {
        //             console.log(error.response);
        //         })
        // },
        // 退出登录按钮
        logoutfunc: function () {
            var url = this.host + '/logout/';
            axios.delete(url, {
                responseType: 'json',
                withCredentials:true,
            })
                .then(response => {
                    location.href = 'login.html';
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 获取购物车数据
       get_cart(){
        let url = this.host + '/carts/simple/';
        axios.get(url, {
            responseType: 'json',
            withCredentials:true,
        })
            .then(response => {
                this.carts = response.data.cart_skus;

                this.cart_total_count = 0;
                for(let i=0;i<this.carts.length;i++){
                    if (this.carts[i].name.length>25){
                        this.carts[i].name = this.carts[i].name.substring(0, 25) + '...';
                    }
                    this.cart_total_count += this.carts[i].count;
                }
            })
            .catch(error => {
                console.log(error);
            })
    },

    }
});