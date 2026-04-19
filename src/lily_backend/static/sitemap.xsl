<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:html="http://www.w3.org/TR/REC-html40"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
	<xsl:template match="/">
		<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
				<title>XML Sitemap - Lily Salon</title>
				<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
				<style type="text/css">
					body {
						font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
						font-size: 14px;
						color: #333;
						margin: 0;
						padding: 40px;
						background-color: #f7f9fc;
					}
					.container {
						max-width: 1000px;
						margin: 0 auto;
						background: #fff;
						padding: 40px;
						border-radius: 12px;
						box-shadow: 0 4px 20px rgba(0,0,0,0.05);
					}
					h1 { color: #1a1a1a; margin-top: 0; font-size: 24px; border-bottom: 2px solid #f0f0f0; padding-bottom: 20px; }
					p { color: #666; line-height: 1.6; }
					table { width: 100%; border-collapse: collapse; margin-top: 30px; }
					th { text-align: left; padding: 12px; border-bottom: 2px solid #eee; color: #999; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }
					td { padding: 15px 12px; border-bottom: 1px solid #f0f0f0; word-break: break-all; }
					tr:hover { background-color: #fcfcfc; }
					a { color: #2563eb; text-decoration: none; }
					a:hover { text-decoration: underline; }
					.lang-tag {
						display: inline-block;
						padding: 2px 6px;
						background: #f0f4ff;
						color: #2563eb;
						border-radius: 4px;
						font-size: 11px;
						font-weight: bold;
						margin-right: 5px;
					}
					.priority-high { color: #059669; font-weight: bold; }
					.priority-low { color: #9ca3af; }
				</style>
			</head>
			<body>
				<div class="container">
					<h1>XML Sitemap</h1>
					<p>This is a machine-readable XML sitemap, used by search engines like Google to index the website. This stylized view is provided for your convenience.</p>

					<table>
						<thead>
							<tr>
								<th>URL</th>
								<th>Priority</th>
								<th>Change Freq.</th>
								<th>Alternates (i18n)</th>
							</tr>
						</thead>
						<tbody>
							<xsl:for-each select="sitemap:urlset/sitemap:url">
								<tr>
									<td>
										<a href="{sitemap:loc}"><xsl:value-of select="sitemap:loc"/></a>
									</td>
									<td>
										<xsl:variable name="p" select="sitemap:priority"/>
										<span class="{if ($p >= 0.8) then 'priority-high' else if ($p &lt; 0.5) then 'priority-low' else ''}">
											<xsl:value-of select="sitemap:priority"/>
										</span>
									</td>
									<td><xsl:value-of select="sitemap:changefreq"/></td>
									<td>
										<xsl:for-each select="xhtml:link">
											<span class="lang-tag"><xsl:value-of select="@hreflang"/></span>
										</xsl:for-each>
									</td>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</div>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>
