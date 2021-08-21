def order_query(cr, ref='ORDER_ID'):
    query = """
WITH partner_rel AS (
	SELECT so.id AS order_id,
		   json_agg(
		   		json_build_object(
					'id', rp.id,
					'name', rp.name,
					'address', rp.street
				)
		   ) AS row_data
	  FROM sale_order so
	  JOIN res_partner rp
	    ON rp.id = so.partner_id
	 WHERE so.id = %s
	 GROUP BY 1
), company_rel AS (
	SELECT so.id AS order_id,
		   json_agg(
		   		json_build_object(
					'id', rc.id,
					'name', rc.name,
					'description', rp.street
				)
		   ) AS row_data
	  FROM sale_order so
	  JOIN res_company rc
	    ON rc.id = so.company_id
	  JOIN res_partner rp
	    ON rp.id = rc.partner_id
	 WHERE so.id = %s
	 GROUP BY 1
), product_rel AS(
    SELECT sol.order_id,
		   jsonb_agg( DISTINCT
				jsonb_build_object(
					'id', pp.id,
					'name', pt.name,
					'price', pt.list_price,
					'description', pp.default_code
				)
		   ) AS row_data
	  FROM sale_order_line sol
	  JOIN product_product pp
	    ON pp.id = sol.product_id
	  JOIN product_template pt
	    ON pt.id = pp.product_tmpl_id
	 WHERE sol.order_id = %s
	 GROUP BY 1
), uom_rel AS (
	SELECT sol.order_id,
		   jsonb_agg( DISTINCT
				jsonb_build_object(
					'id', uu.id,
					'name', uu.name,
					'description', uu.uom_type
				)
		   ) AS row_data
	  FROM sale_order_line sol
	  JOIN uom_uom uu
	    ON uu.id = sol.product_uom
	 WHERE sol.order_id = %s
	 GROUP BY 1
), order_line AS (
    SELECT sol.order_id,
           json_agg(
                json_build_object(
                    'product_id', sol.product_id,
                    'price_unit', sol.price_unit,
                    'product_uom', sol.product_uom,
                    'product_uom_qty', sol.product_uom_qty
                )
	        ) AS row_data
	  FROM sale_order_line sol
	  JOIN sale_order so
	    ON so.id = sol.order_id
	 WHERE so.id = %s
     GROUP BY 1
)
SELECT so.origin AS name,
	   so.partner_id,
	   CAST(so.date_order AS varchar),
	   so.company_id,
	   json_agg(
			json_build_object(
				'partner', partner.row_data,
				'company', company.row_data,
				'product', product.row_data,
				'uom', uom.row_data
			)
	   ) AS relationship,
	   to_json(
		   array_agg(
			   ol.row_data
		   )
	   ) AS order_line
  FROM sale_order so
  JOIN partner_rel partner
    ON so.id = partner.order_id
  JOIN company_rel company
    ON so.id = company.order_id
  JOIN product_rel product
    ON so.id = product.order_id
  JOIN uom_rel uom
    ON so.id = uom.order_id
  JOIN order_line ol
    ON so.id = ol.order_id
 WHERE id = %s
 GROUP BY 1,2,3,4
 """
    params = [ref, ref, ref, ref, ref, ref]
    cr.execute(query, params)
    raw = cr.dictfetchall()
    res = raw[0]
    return res
