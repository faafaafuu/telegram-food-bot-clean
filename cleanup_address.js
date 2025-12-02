// Удаление ненужного элемента addressSuggestions
const fs = require('fs');

const filePath = '/root/telegram-food-bot-clean/webapp/index.html';
let content = fs.readFileSync(filePath, 'utf8');

// Заменяем блок с addressSuggestions на простое поле
content = content.replace(
    /<div style="position: relative;">\s+<input type="text" class="form-input" id="addressInput" placeholder="Начните вводить адрес\.\.\." autocomplete="off">\s+<div id="addressSuggestions"[^>]+><\/div>\s+<\/div>/,
    '<input type="text" class="form-input" id="addressInput" placeholder="Улица, дом, квартира" autocomplete="street-address">'
);

fs.writeFileSync(filePath, content, 'utf8');
console.log('✅ Поле адреса упрощено - теперь обычный input без автодополнения');
