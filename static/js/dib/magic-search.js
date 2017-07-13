Vue.component('dropdown', {
    props: ['options', 'hasFreeText'],
    data: function(){
      return {hasFreeText: this.hasFreeText}
    }
});

Vue.component('search-bar', {
  props: ['filters', 'searchOptions'],
  data: function() {
    return { filters: this.filters,
             curText: '',
             focussed: false,
             selected: false,
           }
  },
  computed: {
    placeholder: function() {
      return (this.filters && this.filters.length > 0) ? '' : 'Filtern und suchen...';
    },
    options: function(){

      let opts = this.selected ? ( this.selected.subSelection ? this.selected.subSelection : [] ) : this.searchOptions;
      if (this.curText) {
        let lowered_text = this.input.toLowerCase();
        return opts.filter((x) => x.name.toLowerCase().indexOf(lowered_text) != -1)
      }
      return opts;
    },
    showList: function() {
      return this.focussed && this.options.length > 0;
    },
    hasFreeText: function () {
      return !this.selected;
    }
  },
  methods: {
    add: function() {
      let msg = this.curText.trim()
      let select = this.selected ? this.selected : {'name': "Suche", 'key': 's'}
      if (msg) {
        this.filters.push({name: select.name, key: select.key , value: msg})
        this.curText = ''
        this.selected = null
      } else {
        // commit search here.
      }
    },
    select: function(item) {
      console.log("selecting", item);
      this.selected = item;
    },
    focus: function () {
      this.focussed = true;
    },
    blur: function () {
      this.focussed = false;
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
      {name: 'Phase', key: 'f'}
    ]
  }
});
