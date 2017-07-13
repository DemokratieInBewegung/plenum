Vue.component('search-bar', {
  props: ['filters'],
  data: function() {
    return { filters: this.filters,
             message: ''
           }
  },
  computed: {placeholder: function() {
      return (this.filters && this.filters.length > 0) ? '' : 'Filtern und suchen...';
    }
  },
  methods: {
    add: function() {
      let msg = this.message.trim()
      if (msg) {
        this.filters.push({name: "Suche", value: msg})
        this.message = ''
      } else {
        // commit search here.
      }
    }
   }
});

var magicSearch = new Vue({
  el: '#magic-search',
  data: {
    filters: [
      {name: 'Suche', value: "Yeah"},
      {name: 'Phase', value: 'Angenommen'}
    ]
  }
});
