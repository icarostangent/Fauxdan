const fs = require('fs')
const path = require('path')

const title = process.argv[2]
if (!title) {
  console.log('Usage: npm run new-post "Post Title"')
  process.exit(1)
}

const date = new Date().toISOString().split('T')[0]
const filename = `${date}-${title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}.md`
const filepath = path.join(__dirname, '../src/data/markdown', filename)

const template = `---
title: ${title}
excerpt: Brief description of the post
date: ${date}
readTime: 5
tags: Tag1, Tag2, Tag3
---

# ${title}

Your content here...
`

fs.writeFileSync(filepath, template)
console.log(`Created new post: ${filename}`)
