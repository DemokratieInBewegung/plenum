Vue.component('dropdown', {
    props: ['options', 'input'],
    // data: function(){
    //   return {input: this.input, options: this.options}
    // },
    computed: {
      filtered: function() {
        // if (!this.input) {
          return this.options;
        // }
      }
    }
});

Vue.component('search-bar', {
  props: ['filters', 'searchOptions'],
  data: function() {
    return { filters: this.filters,
             curText: '',
             selected: false,
           }
  },
  computed: {
    placeholder: function() {
      return (this.filters && this.filters.length > 0) ? '' : 'Filtern und suchen...';
    },
    options: function(){
      if (!this.selected && this.curText){
        return this.searchOptions;
      }
    }
  },
  methods: {
    add: function() {
      let msg = this.curText.trim()
      if (msg) {
        this.filters.push({name: "Suche", value: msg})
        this.curText = ''
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
    ],
    searchOptions: [
      {name: 'Bereich', key: 'b'},
      {name: 'Phase', key: 'f'},
      {name: 'Freitext Suche', key: 's'}
    ]
  }
});
