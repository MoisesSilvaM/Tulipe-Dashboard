window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                selected
            } = context.hideout;
            if (selected.includes(feature.properties.id)) {
                return {
                    fillColor: '#3f3f3f',
                    color: '#3f3f3f'
                }
            }
            //console.log(feature.properties.id)
            return {
                fillColor: '#1a73e8',
                color: '#1a73e8'
            }
        },
        function1: function(feature, layer, context) {
            layer.bindTooltip(`${feature.properties.name} (id:${feature.properties.id})`)
        }
    }
});