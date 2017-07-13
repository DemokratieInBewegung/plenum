var magicSearch = new Vue({
  el: '#magic-search',
  data: {
    message: 'Hello Vue!',
    filters: [
      {name: 'Suche', value: "Yeah"},
      {name: 'Phase', value: 'Angenommen'}
    ]
  },
  methods: {
    add: function() {
      let msg = this.message.trim()
      if (msg) {
        this.filters.push({name: "Suche", value: msg})
        this.message = ''
      }
    }
   }
})