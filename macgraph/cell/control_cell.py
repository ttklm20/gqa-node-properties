
import tensorflow as tf

from ..util import *
from ..attention import *

def control_cell(args, features, in_question_tokens):
	"""
	Build a control cell

	Data in time-minor format

	Arguments:
		- in_control_state.shape   = [batch_size, control_width]
		- in_question_tokens.shape = [batch_size, seq_len, embed_width]

	"""
	with tf.name_scope("control_cell"):

		control_shape = [ features["d_batch_size"], args["control_width"] ]
		question_token_width = args["embed_width"]
		control_query_shape = [ features["d_batch_size"], question_token_width ]

		attention_calls = []
		
		for i in range(args["control_heads"]):
			question_token_query = tf.get_variable(f"control_query_{i}", [1, question_token_width])
			question_token_query = tf.tile(question_token_query, [features["d_batch_size"], 1])
			question_token_query = dynamic_assert_shape(question_token_query, control_query_shape)
			
			a = attention(
				table=in_question_tokens, 
				query=question_token_query, 
				key_width=question_token_width, 
				keys_len=features["src_len"],
			)
			attention_calls.append(a)

		control_out  = [i[0] for i in attention_calls]
		control_out  = tf.concat(control_out, -1)

		tap_qw_attn = [i[1] for i in attention_calls]
		tap_qw_attn = tf.concat(tap_qw_attn, -1) # Concat the unitary score dimensions
		tap_qw_attn = tf.transpose(tap_qw_attn, [0, 2, 1]) # switch so last dimension is words

		if control_out.shape[-1] != args["control_width"]:
			control_out = tf.layers.dense(control_out, args["control_width"], name="resize_control_out")
		
		control_out = dynamic_assert_shape(control_out, control_shape)

		return control_out, tap_qw_attn

