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
        let lowered_text = this.curText.toLowerCase();
        return opts.filter((x) => x.name.toLowerCase().indexOf(lowered_text) != -1)
      }
      return opts;
    },
    showList: function() {
      return this.focussed && this.options.length > 0;
    },
    hasFreeText: function () {
      return !this.selected;
    },
    searchCls: function() {
      return this.selected ? 'badge': '';
    }
  },
  methods: {
    add: function() {
      let msg = this.curText.trim()
      let select = this.selected ? this.selected : {'name': "Suche", 'key': 's'}
      if (msg) {
        this.filters.push({name: select.name, key: select.key , value: msg, label: msg});
        this.curText = '';
        this.selected = null;
        this.$refs.textInput.focus();
      } else {
        // commit search here.
      }
    },
    select: function(item) {
      if (this.selected) {
        this.filters.push({
          name: this.selected.name,
          key: this.selected.key,
          value: item.value,
          label: item.name
        })
        this.selected = null;
      } else {
        this.selected = item;
      }
      this.curText = '';
      this.$refs.textInput.focus();
    },
    focus: function () {
      this.focussed = true;
    },
    blur: function () {
      this.focussed = false;
    },
    clear: function() {
      this.selected = null;
    }
   }
});

var magicSearch = new Vue({
  el: '#magic-search',
  data: {
    filters: [],
    searchOptions: [
      {name: 'Bereich', key: 'b'},
      {name: 'Phase', key: 'f', subSelection: [
        {name: 'In Vorbereitung', value: 'p'},
        {name: 'In Prüfung', value: 'i'},
        {name: 'Sucht Unterstützung', value: 's'},
        {name: 'In Diskussion', value: 'd'},
        {name: 'Finale Überarbeitung', value:'e'},
        {name: 'Finale Prüfung', value:'m'},
        {name: 'Abstimmung', value:'v'},
        {name: 'Angenommen', value:'a'},
        {name: 'Abgelehnt', value:'r'}
      ]}
    ]
  }
});
